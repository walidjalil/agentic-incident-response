#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 20 02:30:43 2026

@author: walidajalil
"""

import pathlib

HADOOP_DIR = pathlib.Path(__file__).parent / "datasets/loghub/hadoop/full"


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


def search_logs(
    application_id: str,
    query: str = None,
    limit: int = 20,
    start_line: int = 1,
):
    application_dir = HADOOP_DIR / application_id
    docs = []
    for txt_file in application_dir.glob("*.log"):
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
            if row_nr < start_line:
                continue
            if query is None or query.lower() in row.lower():
                # list_of_matches.append(row)
                matches.append(
                    {
                        "source": doc["source"],
                        "line": row_nr,
                        "text": row,
                    }
                )
                if limit is not None and len(matches) >= limit:
                    return matches
    if not matches:
        return [{"message": f"No matches found for query: {query}"}]

    return matches
