#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov 28 06:36:39 2026

@author: walidajalil
"""

from pathlib import Path
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-8B")

log_dir = Path("./datasets/loghub/hadoop/full")
total_tokens = 0

files = list(log_dir.rglob("*.log"))

for file in files:
    text = file.read_text(encoding="utf-8", errors="replace")
    tokens = tokenizer.encode(text, add_special_tokens=False)
    total_tokens += len(tokens)

print(f"Total log files: {len(files):,}")
print(f"Total tokens: {total_tokens:,}")
