#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct 16 20:43:46 2026

@author: walidajalil
"""

import os
import requests
import time
import json
import utils
import pathlib

# Extract information from relevant logs.


# What is happening right now?
def get_metrics():
    return {"latency_ms": 850, "gpu_utilization": 32, "queue_length": 47}


# Get information on current deployment and any changes to it.
def get_deployment():
    return {
        "version_before": "v1.8",
        "version_after": "v1.9",
        "changes": {
            "batching_enabled": {
                "before": True,
                "after": False,
            },
        },
    }


# Get information from the logs.
def get_logs(service, limit):
    file_path_pos = pathlib.Path(__file__).parent.resolve()
    file_name = "api_clean.log"

    full_file_name = file_path_pos / file_name

    with open(full_file_name, "r", encoding="utf-8") as file:
        log = file.readlines()

        # # Now 'lines' is a list where each element is a line of text
        # print(log)

    log = log[-limit:]
    # Since log is a list of strings, we need to join them. Since Qwen expects a single large string (not a list)
    log = "".join(log)

    return log


# Return correct tool:
def return_tool(action, tool_args_dict):
    if action == "get_metrics":
        tool_result = get_metrics()
    elif action == "get_deployment":
        tool_result = get_deployment()
    elif action == "get_logs":
        tool_result = get_logs(
            tool_args_dict["service"], tool_args_dict["limit"]
        )
    return tool_result


api_key = os.getenv("RUNPOD_API_KEY")
endpoint_id = os.getenv("RUNPOD_ENDPOINT_ID")

# print("\nAPI key found:", api_key is not None)
# print("Endpoint ID found:", endpoint_id is not None)


url = f"https://api.runpod.ai/v2/{endpoint_id}/runsync"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}

# Chat Completions tool schema (vLLM/OpenAI-compatible format).
# Chat Completions API is slightly different than Reponses API. "type": "function" part is slightly different.

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_metrics",
            "description": "Get the current service metrics.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_deployment",
            "description": "Get information on current deployment and any changes to it.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_logs",
            "description": "Get log posts from various services.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "The service you wish to extract logs from.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "The maximum number of logs rows / posts you wish to extract.",
                    },
                },
                "required": ["service", "limit"],
            },
        },
    },
]


def ask_llm(messages, tools):
    data = {
        "input": {
            "route": "/v1/chat/completions",
            "method": "POST",
            "body": {
                "model": "qwen/qwen3-8b",
                "messages": messages,
                "tools": tools,
                "max_tokens": 1000,
                "temperature": 0.2,
                "chat_template_kwargs": {"enable_thinking": False},
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
            # print(message)
            return message

        time.sleep(7)


messages = [
    {
        "role": "system",
        "content": "Use the available tools when needed.",
    },
    {
        "role": "user",
        "content": "The API service is slow and returning errors. Investigate the problem.",
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
                "content": "Maximum tool iterations reached. Give your best final answer using the information gathered so far.",
            }
        )

        final_answer = ask_llm(messages, [])

        print("\nAgent stopped: maximum iterations reached.")
        print("Final answer:")
        print(final_answer["content"])
        break

    agentic_iterations += 1

    answer = ask_llm(messages, tools)
    messages.append(answer)

    if answer.get("tool_calls"):
        for a in answer["tool_calls"]:
            tool_name = a["function"]["name"]

            tool_args_dict = json.loads(a["function"]["arguments"])
            # print(tool_args_dict)

            print("\nQwen chose: ", tool_name)

            tool_result = return_tool(tool_name, tool_args_dict)
            print("\nTool result:\n")
            print(tool_result)

            ### Native tool calling can call on multiple functions in the same answer. Make sure you REMEMBER that!
            new_message = {
                "role": "tool",
                "tool_call_id": a["id"],
                "content": json.dumps(tool_result),
            }
            messages.append(new_message)

    # If no tool call is returned, treat the response as final.
    else:
        print("\n")
        print(answer["content"])
        break


# Bla bla bla
# Bla bla bla
