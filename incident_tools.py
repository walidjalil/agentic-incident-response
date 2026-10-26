#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 20 02:30:43 2026

@author: walidajalil
"""

import pathlib

HADOOP_DIR = pathlib.Path(__file__).parent / "datasets/loghub/hadoop"


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


# Extract information from relevant logs.
def get_logs(service, limit):
    service_files = {
        "api": "api_ambigious.log",
        "worker": "worker.log",
        "db": "db.log",
    }
    file_path_pos = pathlib.Path(__file__).parent.resolve()
    file_name = service_files[service]

    full_file_name = file_path_pos / "logs" / file_name

    with open(full_file_name, "r", encoding="utf-8") as file:
        log = file.readlines()

    log = log[-limit:]
    # Since log is a list of strings, we need to join them. Since Qwen expects a single large string (not a list)
    log = "".join(log)

    return log


def search_logs(query: str = None, limit: int = 20):
    docs = []
    for txt_file in HADOOP_DIR.glob("*.log"):
        with open(txt_file) as f:
            docs.append(
                {
                    "source": txt_file.name,
                    "text": f.readlines(),
                }
            )
    matches = []
    for doc in docs:
        for row_nr, row in enumerate(doc["text"], start=1):
            if query is None or query.lower() in row.lower():
                # list_of_matches.append(row)
                matches.append(
                    {
                        "source": doc["source"],
                        "line": row_nr,
                        "text": row,
                    }
                )
                if len(matches) >= limit:
                    return matches
    return matches
