#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct 16 20:43:46 2026

@author: walidajalil
"""

from mcp_client import get_tool_definitions, call_mcp_tool
import anyio
import os
import requests
import time
import json
import utils


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
    data = {
        "input": {
            "route": "/v1/chat/completions",
            "method": "POST",
            "body": {
                "model": "qwen/qwen3-8b",
                "messages": messages,
                "tools": tool_definitions,
                "max_tokens": 2000,
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

        status_data = status_response.json()

        print("\nCurrent status:", status_data["status"])

        # Code block to Print the message if status is completed.
        if status_data["status"] == "COMPLETED":
            message = status_data["output"][0]["choices"][0]["message"]
            return message

        time.sleep(10)


if __name__ == "__main__":
    tool_definitions = anyio.run(get_tool_definitions)

    messages = [
        {
            "role": "system",
            "content": "Use the available tools when needed.",
        },
        {
            "role": "user",
            "content": "The API service is slow and returning errors. Investigate the problem. If evidence points to another service, inspect that service's logs before declaring it a root cause.",
        },
    ]

    max_agentic_iterations = 5
    agentic_iterations = 0

    while True:
        # Stop safely if the agent reaches the iteration limit.
        if agentic_iterations >= max_agentic_iterations:
            messages.append(
                {
                    "role": "user",
                    "content": "Maximum agent iterations reached. Give your best final answer using the information gathered so far.",
                }
            )

            final_answer = ask_llm(messages, [])

            print("\nAgent stopped: maximum agent iterations reached.")
            print("Final answer:")
            print(utils.remove_thinking(final_answer["content"]))
            break

        agentic_iterations += 1

        answer = ask_llm(messages, tool_definitions)
        messages.append(answer)

        if answer.get("tool_calls"):
            for a in answer["tool_calls"]:
                tool_name = a["function"]["name"]

                tool_args_dict = json.loads(a["function"]["arguments"])

                print("\nQwen chose: ", tool_name)
                print("Arguments:", tool_args_dict)

                tool_result = anyio.run(
                    call_mcp_tool, tool_name, tool_args_dict
                )
                print("\nTool result:\n")
                print(tool_result)

                # Native tool calling can call on multiple functions in the same answer. Make sure you REMEMBER that!
                new_message = {
                    "role": "tool",
                    "tool_call_id": a["id"],
                    "content": tool_result,
                }
                messages.append(new_message)

        # If no tool call is returned, treat the response as final.
        else:
            print("\n")
            print(utils.remove_thinking(answer["content"]))
            break
