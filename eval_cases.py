#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 29 10:33:01 2026

@author: walidajalil
"""

from incident_tools import search_logs
import csv

from agent import run_agent
import anyio

result = search_logs(
    application_id="application_1445062781478_0011",
    query=None,
    limit=1000,
)


def load_labels():
    labels = {}

    with open("datasets/loghub/hadoop/full/hadoop_labels.csv") as f:
        reader = csv.DictReader(f)

        for row in reader:
            labels[row["application_id"]] = row["label"]

    return labels


results = load_labels()

test_ids = [
    "application_1445062781478_0011",
    "application_1445062781478_0012",
    "application_1445144423722_0020",
    "application_1445182159119_0011",
]


async def evaluate_case(application_id=None, expected_label=None):
    prompt = [
        {
            "role": "system",
            "content": "Use the available tools when needed.",
        },
        {
            "role": "user",
            "content": """Investigate Hadoop application "application_1445062781478_0012" using the available tools. Be thorough.
    
    Classify the application as exactly one of:
    - Normal
    - Machine down
    - Network disconnection
    - Disk full
    
    Return your final answer as valid JSON with exactly these fields:
- "label": one of "Normal", "Machine down", "Network disconnection", "Disk full"
- "explanation": a short explanation of the evidence""",
        },
    ]

    return run_agent(prompt)


data = anyio.run(evaluate_case)
