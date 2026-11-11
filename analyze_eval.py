#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 11 23:24:45 2026

@author: walidajalil
"""

import json
from pathlib import Path
import numpy as np


def load_eval_results():
    runs = {}

    for file_path in sorted(Path(".").glob("eval_results_run*.jsonl")):
        results = []

        with open(file_path) as f:
            for line in f:
                results.append(json.loads(line))

        runs[file_path.stem] = results

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


def calc_mean(accuracies):
    return np.array(list(accuracies.values())).mean()


def calc_std(accuracies):
    return np.array(list(accuracies.values())).std(ddof=1)


mean = calc_mean(accuracies)
std = calc_std(accuracies)
