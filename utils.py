#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 13 16:14:07 2026

@author: walidajalil
"""

import json
import re

# Code to print nested trees:


def print_tree(data, prefix=""):
    if isinstance(data, dict):
        items = list(data.items())

        for i, (key, value) in enumerate(items):
            is_last = i == len(items) - 1
            connector = "└── " if is_last else "├── "

            print(prefix + connector + str(key))

            new_prefix = prefix + ("    " if is_last else "│   ")
            print_tree(value, new_prefix)


# Check whether the variable is a JSON.
def is_json(myjson):
    try:
        json.loads(myjson)
    except ValueError:
        return False
    return True


# Remove thinking part from output tokens in answer:
def remove_thinking(answer):
    return re.sub(r"<think>.*?</think>", "", answer, flags=re.DOTALL).strip()
