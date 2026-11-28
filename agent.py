#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct 16 20:43:46 2026

@author: walidajalil
"""

from mcp import Client
from mcp_client import server_params, get_tool_definitions, call_mcp_tool
import anyio
import os
import requests
import time
import json
import utils
from context_budget import fit_context, MAX_OUTPUT_TOKENS


api_key = os.getenv("RUNPOD_API_KEY")
endpoint_id = os.getenv("RUNPOD_ENDPOINT_ID")


url = f"https://api.runpod.ai/v2/{endpoint_id}/runsync"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}

# Chat Completions tool schema (vLLM/OpenAI-compatible format).
# Chat Completions API is slightly different than Responses API. "type": "function" part is slightly different.


def ask_llm(messages, tool_definitions=None):
    messages = fit_context(messages, tool_definitions or [])
    data = {
        "input": {
            "route": "/v1/chat/completions",
            "method": "POST",
            "body": {
                "model": "qwen/qwen3-8b",
                "messages": messages,
                "tools": tool_definitions,
                "max_tokens": MAX_OUTPUT_TOKENS,
                "temperature": 0.2,
                "chat_template_kwargs": {"enable_thinking": True},
            },
        }
    }

    response = requests.post(
        url,
        headers=headers,
        json=data,
    )

    result = response.json()

    job_id = result["id"]
    status_url = f"https://api.runpod.ai/v2/{endpoint_id}/status/{job_id}"

    while True:
        status_response = requests.get(
            status_url,
            headers=headers,
        )

        # Stop if the HTTP request itself failed (e.g. 404).
        status_response.raise_for_status()

        status_data = status_response.json()
        status = status_data["status"]

        print("\nCurrent status:", status)

        # Code block to return the message if status is completed.
        if status == "COMPLETED":
            message = status_data["output"][0]["choices"][0]["message"]
            return message

        # Stop polling if RunPod reports a failed job.
        if status in ("FAILED", "CANCELLED", "TIMED_OUT"):
            print("RunPod error:", status_data)
            raise RuntimeError(f"RunPod job {status}")

        time.sleep(10)


def prepare_context(prompt):
    return prompt


async def run_agent(prompt):
    async with Client(server_params) as client:
        tool_definitions = await get_tool_definitions(client)

        #     messages = [
        #         {
        #             "role": "system",
        #             "content": "Use the available tools when needed.",
        #         },
        #         {
        #             "role": "user",
        #             "content": """The API has become significantly slower and is returning intermittent 5xx errors.
        # Investigate the incident, determine the most likely root cause, and explain what evidence supports your conclusion.
        # Use any available tools or documentation that would help.""",
        #         },
        #     ]

        max_agentic_iterations = 10
        agentic_iterations = 0

        while True:
            # Stop safely if the agent reaches the iteration limit.
            if agentic_iterations >= max_agentic_iterations:
                prompt.append(
                    {
                        "role": "user",
                        "content": "Maximum agent iterations reached. Give your best final answer using the information gathered so far.",
                    }
                )
                context = prepare_context(prompt)

                for msg in context:
                    if msg["role"] == "tool":
                        print(
                            "Tool result length:",
                            len(msg["content"]),
                            "Contains lost:",
                            "lost" in msg["content"].lower(),
                        )

                print(
                    "Original context:",
                    sum(len(str(m)) for m in prompt),
                    "characters",
                )
                print(
                    "Prepared context:",
                    sum(len(str(m)) for m in context),
                    "characters",
                )

                final_answer = ask_llm(context, [])

                print("\nAgent stopped: maximum agent iterations reached.")
                print("Final answer:")
                print(utils.remove_thinking(final_answer["content"]))
                return utils.remove_thinking(final_answer["content"])

            agentic_iterations += 1

            context = prepare_context(prompt)

            for msg in context:
                if msg["role"] == "tool":
                    print(
                        "Tool result length:",
                        len(msg["content"]),
                        "Contains lost:",
                        "lost" in msg["content"].lower(),
                    )

            print(
                "Original context:",
                sum(len(str(m)) for m in prompt),
                "characters",
            )
            print(
                "Prepared context:",
                sum(len(str(m)) for m in context),
                "characters",
            )

            answer = ask_llm(context, tool_definitions)
            prompt.append(answer)

            if answer.get("tool_calls"):
                for a in answer["tool_calls"]:
                    tool_name = a["function"]["name"]

                    tool_args_dict = json.loads(a["function"]["arguments"])

                    # print("\nQwen chose: ", tool_name)
                    # print("Arguments:", tool_args_dict)

                    tool_result = await call_mcp_tool(
                        client,
                        tool_name,
                        tool_args_dict,
                    )
                    # print("\nTool result:\n")
                    # print(tool_result)

                    # Native tool calling can call on multiple functions in the same answer. Make sure you REMEMBER that!
                    new_message = {
                        "role": "tool",
                        "tool_call_id": a["id"],
                        "content": tool_result,
                    }
                    prompt.append(new_message)

            # If no tool call is returned, treat the response as final.
            else:
                print("\n")
                final_answer = utils.remove_thinking(answer["content"])
                print(final_answer)
                return final_answer


async def main():
    prompt = [
        {
            "role": "system",
            "content": "Use the available tools when needed.",
        },
        {
            "role": "user",
            "content": """Investigate Hadoop application "application_1445144423722_0022"
using the available tools.

Classify the application as exactly one of:
- Normal
- Machine down
- Network disconnection
- Disk full

Search instructions:
- BM25 uses lexical matching, so use short, focused queries.
- Perform at least two separate searches targeting different failure indicators.
- Search separately for node availability, container failures, network connectivity, and storage problems.
- Include at least one query targeting node availability, using terms such as "node" or "lost".
- Do not combine all failure categories into one BM25 query.
- Relevant evidence may appear in INFO logs, not only WARN or ERROR.

Diagnostic guidance:
- Distinguish observed symptoms from the most likely underlying cause.
- Connection errors can occur when a machine becomes unavailable.
- A lost-node message establishes that Hadoop considers a node unavailable; it does not establish why.
- Continued local logging supports process activity, but does not by itself establish Network disconnection.
- Consider affected hosts, affected services, event order, and recovery together.
- A job can succeed despite an injected failure.

The following examples illustrate how to weigh evidence.
They do not describe the application you are investigating.
Do not treat their patterns as definitive rules.

Example 1

Evidence:
Four task logs on the same worker stop during ordinary processing.
Both its NodeManager and DataNode endpoints become unavailable.
Other workers continue, and the job succeeds.
Later, Hadoop reports the worker as unusable and releases its containers.

Answer:
{
  "label": "Machine down",
  "explanation": "The combined evidence supports host-wide unavailability: colocated tasks stop logging and multiple services on the same worker become inaccessible. Connection errors are symptoms of that unavailability. A network partition cannot be ruled out from these logs alone."
}

Example 2

Evidence:
The affected ApplicationMaster continues logging locally for over
23 minutes while failing to reach RM and HDFS.
Tasks on other hosts also lose communication with that AM.
The first application attempt enters ERROR; a later attempt succeeds.

Answer:
{
  "label": "Network disconnection",
  "explanation": "Continued local activity together with failures across several incoming and outgoing communication paths supports network isolation. The precise physical cause remains uncertain."
}

Now investigate application "application_1445144423722_0022".

Base your final explanation only on evidence retrieved for this
application, not on observations from the examples.

Return valid JSON with exactly these fields:
- "label": one of the four allowed labels
- "explanation": a short explanation of the supporting evidence and any important uncertainty""",
        },
    ]

    result = await run_agent(prompt)
    return result


if __name__ == "__main__":
    final_answer = anyio.run(main)
