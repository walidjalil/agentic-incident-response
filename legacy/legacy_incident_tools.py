#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pathlib


# Return simulated service metrics.
def get_metrics():
    return {
        "latency_ms": 850,
        "gpu_utilization": 32,
        "queue_length": 47,
    }


# Return information about the latest deployment.
def get_deployment():
    return {
        "version_before": "v1.8",
        "version_after": "v1.9",
        "changes": {
            "batching_enabled": {
                "before": True,
                "after": False,
            }
        },
    }


# Extract information from relevant logs.
def get_logs(service, limit):
    service_files = {
        "api": "api_ambigious.log",
        "worker": "worker.log",
        "db": "db.log",
    }

    project_root = pathlib.Path(__file__).parent.parent.resolve()
    file_name = service_files[service]

    full_file_name = project_root / "logs" / file_name

    with open(full_file_name, "r", encoding="utf-8") as file:
        log = file.readlines()

    log = log[-limit:]

    # Since log is a list of strings, join it into one large string.
    log = "".join(log)

    return log


# Legacy direct tool router used by the pre-MCP agent.
def return_tool(action, tool_args_dict):
    if action == "get_metrics":
        tool_result = get_metrics()
    elif action == "get_deployment":
        tool_result = get_deployment()
    elif action == "get_logs":
        tool_result = get_logs(
            tool_args_dict["service"],
            tool_args_dict["limit"],
        )
    else:
        raise ValueError(f"Unknown tool: {action}")

    return tool_result
