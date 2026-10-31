#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 29 10:33:01 2026

@author: walidajalil
"""

import csv
import json
from agent import run_agent
import anyio


def load_labels():
    labels = {}

    with open("datasets/loghub/hadoop/full/hadoop_labels.csv") as f:
        reader = csv.DictReader(f)

        for row in reader:
            labels[row["application_id"]] = row["label"]

    return labels


results = load_labels()


async def evaluate_case(application_id, expected_label):
    prompt = [
        {
            "role": "system",
            "content": "Use the available tools when needed.",
        },
        {
            "role": "user",
            "content": f"""Investigate Hadoop application {application_id} using the available tools. Be thorough.
    
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
    output = await run_agent(prompt)
    output = json.loads(output)

    return {
        "application_id": application_id,
        "expected": expected_label,
        "predicted": output["label"],
        "correct": output["label"] == expected_label,
        "explanation": output["explanation"],
    }


async def main():
    step_counter = 1
    evaluations = []

    for application_id, expected_label in results.items():
        print("Step: ", step_counter)

        result = await evaluate_case(application_id, expected_label)
        evaluations.append(result)

        with open("eval_results.jsonl", "a") as f:
            f.write(json.dumps(result) + "\n")

        step_counter += 1

    correct = sum(result["correct"] for result in evaluations)
    total = len(evaluations)

    print(f"\nCorrect: {correct}/{total}")
    print(f"Accuracy: {correct / total:.1%}")

    return evaluations


evaluations = anyio.run(main)
