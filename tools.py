#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 20 02:30:43 2026

@author: walidajalil
"""

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


# Get information from various logs.
def get_logs(service, limit):
    service_files = {
        "api": "api_ambigious.log",
        "worker": "worker.log",
        "db": "db.log",
    }
    file_path_pos = pathlib.Path(__file__).parent.resolve()
    file_name = service_files[service]

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
