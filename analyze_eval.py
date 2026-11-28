#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 11 23:24:45 2026

@author: walidajalil
"""

import json
from pathlib import Path
import numpy as np
from collections import Counter


def load_eval_results():
    runs = {}

    for file_path in sorted(
        Path(".").glob(
            "eval_results/eval_results_fewshot_v2_clean_run_with_tools*.jsonl"
        )
    ):
        results = []

        with open(file_path) as f:
            for line in f:
                results.append(json.loads(line))

        runs[file_path.stem] = results[-55:]

    return runs


runs = load_eval_results()


def accuracy_per_run(runs):
    accuracies = {}

    for run_name, results in runs.items():
        correct = sum(result["correct"] for result in results)
        total = len(results)

        accuracies[run_name] = correct / total

    return accuracies


accuracies = accuracy_per_run(runs)
print(accuracies)
print("----------------------------------")

def calc_mean(accuracies):
    return np.array(list(accuracies.values())).mean()


def calc_std(accuracies):
    return np.array(list(accuracies.values())).std(ddof=1)


mean = calc_mean(accuracies)
std = calc_std(accuracies)


def confusion_counts(runs):
    counts = Counter()

    for results in runs.values():
        for result in results:
            key = (result["expected"], result["predicted"])
            counts[key] += 1

    return counts


print(confusion_counts(runs))

labels = [
    "Normal",
    "Machine down",
    "Network disconnection",
    "Disk full",
]

matrix = np.zeros((4, 4), dtype=int)

for results in runs.values():
    for result in results:
        true_idx = labels.index(result["expected"])
        pred_idx = labels.index(result["predicted"])
        matrix[true_idx, pred_idx] += 1

print(matrix)


# Calculate Precision, recall and F1 for each class.
def calc_metrics(matrix, labels):
    metrics = {}

    for i, label in enumerate(labels):
        true_positive = matrix[i, i]

        actual_total = matrix[i, :].sum()
        predicted_total = matrix[:, i].sum()

        recall = true_positive / actual_total
        precision = true_positive / predicted_total

        f1 = 2 * precision * recall / (precision + recall)

        metrics[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": actual_total,
        }

    return metrics


metrics = calc_metrics(matrix, labels)

for label, values in metrics.items():
    print(label, values)


# mean F1 for all classes:
macro_f1 = np.mean([values["f1"] for values in metrics.values()])

# weighted F1 because each class does not appear in equal numbers.
total = sum(values["support"] for values in metrics.values())
weighted_f1 = (
    sum(values["f1"] * values["support"] for values in metrics.values())
    / total
)
