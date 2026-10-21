#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 13 15:33:35 2026

@author: walidajalil
"""

import os
import requests
import time
import json
import utils


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


# Check whether the LLM answer is the right format.
def parse_answer(answer, available_tools):
    if utils.is_json(answer):
        parsed_answer = json.loads(answer)
        if isinstance(parsed_answer, dict):
            key = "action"
            if key in parsed_answer:
                action = parsed_answer["action"].strip()
                if action in available_tools:
                    return action
                else:
                    print(
                        "The LLM chose a tool that wasn't available in the toolbox."
                    )
                    return None
            else:
                print("The dictionary didn't have an action key.")
        else:
            print("The LLM did not return a dict.")

    else:
        print("The LLM did not return a JSON.")


# Return correct tool:
def return_tool(action):
    if action == "metrics":
        tool_result = get_metrics()
    elif action == "deployment":
        tool_result = get_deployment()
    return tool_result


metrics = get_metrics()
deployment = get_deployment()


print("Metrics:")
print(metrics)

print("\nDeployment:")
print(deployment)


""" Print function tree: """
# print("\nDeployment tree:\n")
# utils.print_tree(deployment)

api_key = os.getenv("RUNPOD_API_KEY")
endpoint_id = os.getenv("RUNPOD_ENDPOINT_ID")

print("\nAPI key found:", api_key is not None)
print("Endpoint ID found:", endpoint_id is not None)

url = f"https://api.runpod.ai/v2/{endpoint_id}/runsync"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}


def ask_llm(prompt):
    data = {
        "input": {
            "route": "/v1/chat/completions",
            "method": "POST",
            "body": {
                "model": "qwen/qwen3-8b",
                "messages": [
                    {
                        "role": "system",
                        "content": "Please answer in short sentences.",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                "max_tokens": 200,
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
    print(result)

    job_id = result["id"]
    status_url = f"https://api.runpod.ai/v2/{endpoint_id}/status/{job_id}"

    while True:
        status_response = requests.get(
            status_url,
            headers=headers,
        )

        status_data = status_response.json()

        print("Current status:", status_data["status"])

        if status_data["status"] == "COMPLETED":
            content = status_data["output"][0]["choices"][0]["message"][
                "content"
            ]
            return content

        time.sleep(5)


observations = []
available_tools = ["metrics", "deployment"]

while available_tools:
    # print("step: ", str(i + 1))

    prompt = f"""
The service became slow after the latest deployment.

Available tools: {available_tools}
Observations so far:
{observations}

What should you inspect next?
Reply as JSON with one key called "action".
The value must be one of the available tools above.
"""

    answer = ask_llm(prompt)
    print(answer)

    action = parse_answer(answer, available_tools)

    if action is None:
        break

    tool_result = return_tool(action)

    available_tools.remove(action)

    observation = {action: tool_result}
    observations.append(observation)

print(observations)

final_prompt = f""" The service became slow after the latest deployment. These are the following
observations you have made: {observations}. 

Can you give us a diagnosis of the problem? If no observations have been made, 
state that that no observations have been made."""

final_answer = ask_llm(final_prompt)
print("\nDiagnosis: ", final_answer)
