from bisect import bisect_right
from copy import deepcopy
from functools import lru_cache
import json
import re

MODEL_CONTEXT_TOKENS = 40_960
MAX_OUTPUT_TOKENS = 6_000
MAX_INPUT_TOKENS = 28_000
MIN_EXCERPT_BUDGET = 128


@lru_cache(maxsize=1)
def get_tokenizer():
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained("Qwen/Qwen3-8B", use_fast=True)


def count_input_tokens(messages, tools, tokenizer):
    tokens = tokenizer.apply_chat_template(
        messages,
        tools=tools or None,
        tokenize=True,
        return_dict=False,
        add_generation_prompt=True,
        enable_thinking=True,
    )
    return len(tokens)


def _query_terms(messages):
    queries = {}
    for message in messages:
        for call in message.get("tool_calls") or []:
            args = call.get("function", {}).get("arguments", {})
            try:
                args = json.loads(args) if isinstance(args, str) else args
            except (ValueError, TypeError):
                args = {}
            queries[call.get("id")] = (
                str(args.get("query", "")) if isinstance(args, dict) else ""
            )
    return queries


def _encode_result(text, query, tokenizer):
    encoded = tokenizer(
        text, add_special_tokens=False, return_offsets_mapping=True
    )
    offsets = encoded["offset_mapping"]
    starts = [a for a, _ in offsets]
    anchors = []
    # No failure-class rules: anchors come only from this tool's search query.
    terms = list(dict.fromkeys(re.findall(r"[\w-]{3,}", query.lower())))[:6]
    for term in terms:
        matches = list(re.finditer(re.escape(term), text, re.IGNORECASE))
        if matches:
            for match in (matches[0], matches[-1]):
                anchors.append(max(0, bisect_right(starts, match.start()) - 1))
    return dict(text=text, offsets=offsets, anchors=sorted(set(anchors)))


def _excerpt(record, budget):
    text, offsets, anchors = (
        record["text"],
        record["offsets"],
        record["anchors"],
    )
    n = len(offsets)
    if n <= budget:
        return text
    centers = sorted(set([0, n - 1, *anchors]))
    width = max(1, budget // len(centers))
    ranges = []
    for center in centers:
        start = max(0, min(center - width // 2, n - width))
        end = min(n, start + width)
        left, right = offsets[start][0], offsets[end - 1][1]
        if right > left:
            ranges.append((left, right))
    merged = []
    for left, right in sorted(ranges):
        if merged and left <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(right, merged[-1][1]))
        else:
            merged.append((left, right))
    warning = (
        "[TOOL OUTPUT ABBREVIATED to fit the input budget. Text between excerpts "
        "is omitted. Missing text is unknown; do not infer that a failure is absent. "
        "Excerpts may be fragments of the original JSON, not standalone JSON.]\n"
    )
    return warning + "\n".join(
        f"[Original tool-response characters {left}:{right}]\n{text[left:right]}"
        for left, right in merged
    )


def fit_context(
    messages,
    tools=None,
    *,
    tokenizer=None,
    max_input_tokens=MAX_INPUT_TOKENS,
    verbose=True,
):
    """Return a budgeted COPY; retain tool-call/result pairs and the initial prompt.

    First shorten older tool outputs, then current outputs. Only if all are
    already minimal and the chat is still too large, remove the oldest completed
    tool-call round. Never silently send an oversized request.
    """
    if not 0 < max_input_tokens <= MODEL_CONTEXT_TOKENS - MAX_OUTPUT_TOKENS:
        raise ValueError("Input budget must leave room for output tokens.")
    tokenizer = tokenizer or get_tokenizer()
    tools = tools or []
    context = deepcopy(messages)
    queries = _query_terms(context)
    records, caps, changed = {}, {}, set()
    removed_rounds = 0
    for message in context:
        if message.get("role") == "tool" and isinstance(
            message.get("content"), str
        ):
            key = id(message)
            records[key] = _encode_result(
                message["content"],
                queries.get(message.get("tool_call_id"), ""),
                tokenizer,
            )
            caps[key] = len(records[key]["offsets"])
    while True:
        size = count_input_tokens(context, tools, tokenizer)
        if size <= max_input_tokens:
            if verbose:
                print(
                    f"Budgeted input: {size}/{max_input_tokens} tokens; "
                    f"shortened tool results: {len(changed)}; removed old rounds: {removed_rounds}"
                )
            return context
        call_positions = [
            i
            for i, m in enumerate(context)
            if m.get("role") == "assistant" and m.get("tool_calls")
        ]
        latest = call_positions[-1] if call_positions else -1
        candidates = [
            (i, m)
            for i, m in enumerate(context)
            if id(m) in caps and caps[id(m)] > MIN_EXCERPT_BUDGET
        ]
        if candidates:
            older = [(i, m) for i, m in candidates if i < latest]
            _, target = max(
                older or candidates, key=lambda pair: caps[id(pair[1])]
            )
            key = id(target)
            caps[key] = max(MIN_EXCERPT_BUDGET, caps[key] // 2)
            target["content"] = records[key].get("prefix", "") + _excerpt(
                records[key], caps[key]
            )
            changed.add(key)
            continue
        if len(call_positions) > 1:
            first = call_positions[0]
            call_ids = {c["id"] for c in context[first]["tool_calls"]}
            context = [
                m
                for i, m in enumerate(context)
                if i != first
                and not (
                    m.get("role") == "tool"
                    and m.get("tool_call_id") in call_ids
                )
            ]
            removed_rounds += 1
            note = (
                "[CONTEXT NOTE: An earlier tool-call round was omitted for size. "
                "Its observations are unavailable here, not evidence that failures were absent.]\n"
            )
            # Label the omission without changing roles or tool-call IDs.
            for m in context:
                if m.get("role") == "tool":
                    key = id(m)
                    if key in records:
                        records[key]["prefix"] = note
                        m["content"] = note + _excerpt(records[key], caps[key])
                    break
            continue
        raise ValueError(
            f"Input still has {size} tokens after tool excerpts were minimized. "
            "The fixed prompt/assistant messages/tool schemas exceed the budget; "
            "no request was sent to RunPod."
        )
