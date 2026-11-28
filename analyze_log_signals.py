#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 25 05:55:42 2026

@author: walidajalil
"""

from pathlib import Path
from incident_tools import load_application_logs

# Ground-truth labels from LogHub.
label_file = (
    Path(__file__).resolve().parent
    / "datasets/loghub/hadoop/full/abnormal_label.txt"
)

labels = [
    "Normal",
    "Machine down",
    "Network disconnection",
    "Disk full",
]

workloads = ["WordCount", "PageRank"]

# Store statistics for each workload and failure class.
results = {
    (workload, label): {
        "applications": 0,
        "with_lost_node": 0,
        "total_matches": 0,
    }
    for workload in workloads
    for label in labels
}

current_workload = None
current_label = None

# Read the ground-truth file.
for line in label_file.read_text().splitlines():
    line = line.strip()

    # Identify the workload: WordCount or PageRank.
    if line.startswith("### "):
        current_workload = line.removeprefix("### ").strip()
        current_label = None
        continue

    # Identify the failure class.
    if line.endswith(":") and line[:-1] in labels:
        current_label = line[:-1]
        continue

    # Process each labeled Hadoop application.
    if (
        line.startswith("+ application_")
        and current_workload in workloads
        and current_label in labels
    ):
        application_id = line.removeprefix("+ ").strip()

        docs = load_application_logs(application_id)

        # Count log lines indicating containers on lost nodes.
        matches = sum(
            "container released on a" in doc["text"].lower()
            and "lost" in doc["text"].lower()
            and "node" in doc["text"].lower()
            for doc in docs
        )

        data = results[(current_workload, current_label)]

        data["applications"] += 1
        data["with_lost_node"] += int(matches > 0)
        data["total_matches"] += matches


# Print results grouped by workload.
for workload in workloads:
    print(f"\n{'=' * 45}")
    print(f"{workload}")
    print(f"{'=' * 45}")

    for label in labels:
        data = results[(workload, label)]

        total = data["applications"]
        found = data["with_lost_node"]
        percentage = 100 * found / total if total else 0

        print(
            f"{label}: {found}/{total} "
            f"({percentage:.1f}%) "
            f"| Matching log lines: {data['total_matches']}"
        )


# Print overall statistics across both workloads.
print(f"\n{'=' * 45}")
print("OVERALL")
print(f"{'=' * 45}")

for label in labels:
    total = sum(
        results[(workload, label)]["applications"] for workload in workloads
    )

    found = sum(
        results[(workload, label)]["with_lost_node"] for workload in workloads
    )

    percentage = 100 * found / total if total else 0

    print(f"{label}: {found}/{total} ({percentage:.1f}%)")
