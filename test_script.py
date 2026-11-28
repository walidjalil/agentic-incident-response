#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 25 03:00:30 2026

@author: walidajalil
"""

from incident_tools import load_application_logs


app = "application_1445062781478_0012"
docs = load_application_logs(app)

patterns = [
    "lost",
    "unreachable",
    "connection",
    "timeout",
    "failed",
    "killed",
    "bad connect",
    "exclud",
    "exception",
]

"""
for pattern in patterns:
    matches = [doc for doc in docs if pattern in doc["text"].lower()]

    print(f"\n{pattern}: {len(matches)} matches")

    for doc in docs:
        if "lost" in doc["text"].lower():
            print(f"\n{doc['source']}:{doc['line']}")
            print(doc["text"])
"""

from incident_tools import search_logs_bm25_v2

app = "application_1445062781478_0012"

"""
matches = search_logs_bm25_v2(
    application_id=app, query="lost node", limit=5, chunk_size=50, overlap=10
)

for i, chunk in enumerate(matches, 1):
    if "text" not in chunk:
        print(chunk)
        continue

    print(f"\nRank {i}: {chunk['source']}")
    print(f"Lines: {chunk['start_line']}–{chunk['end_line']}")

    for line in chunk["text"].splitlines():
        if "lost" in line.lower():
            print(line)

"""
matches = search_logs_bm25_v2(
    application_id=app, query="node", limit=5, chunk_size=50, overlap=10
)

for i, chunk in enumerate(matches, 1):
    if "text" not in chunk:
        continue

    print(
        f"Rank {i}: {chunk['source']} "
        f"({chunk['start_line']}–{chunk['end_line']})"
    )
    print("Contains 'lost':", "lost" in chunk["text"].lower())


from incident_tools import load_application_log_chunks

docs = load_application_log_chunks(app, chunk_size=50, overlap=10)

matches = [doc for doc in docs if "node" in doc["text"].lower()]

print("Total chunks:", len(docs))
print("Chunks containing 'node':", len(matches))


import re

exact_matches = [
    doc for doc in docs if re.search(r"\bnode\b", doc["text"], re.IGNORECASE)
]

print("Substring matches:", len(matches))
print("Whole-word matches:", len(exact_matches))


matches = search_logs_bm25_v2(
    application_id=app,
    query="error failure disk network machine container",
    limit=5,
    chunk_size=50,
    overlap=10,
)

for i, chunk in enumerate(matches, 1):
    if "text" not in chunk:
        continue

    print(f"Rank {i}: {chunk['source']}")
    print(f"Lines: {chunk['start_line']}–{chunk['end_line']}")
    print("Contains 'lost':", "lost" in chunk["text"].lower())


from incident_tools import load_application_logs

app = "application_1445144423722_0020"
docs = load_application_logs(app)

matches = [
    doc
    for doc in docs
    if "container released on a" in doc["text"].lower()
    and "lost" in doc["text"].lower()
    and "node" in doc["text"].lower()
]

print("")
print("--------------------------------------------------------")
print("Total log lines:", len(docs))
print("Total log files:", len(set(doc["source"] for doc in docs)))
print("Lost node matches:", len(matches))

for doc in matches:
    print(f"{doc['source']}:{doc['line']} {doc['text'].strip()}")
