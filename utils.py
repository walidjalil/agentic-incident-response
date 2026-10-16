#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 13 16:14:07 2026

@author: walidajalil
"""

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
