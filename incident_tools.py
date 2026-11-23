#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 20 02:30:43 2026

@author: walidajalil
"""

import pathlib
import bm25s

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


def load_application_logs(application_id):
    application_dir = HADOOP_DIR / application_id
    docs = []

    for txt_file in application_dir.glob("*.log"):
        with open(txt_file) as f:
            for line_nr, line_text in enumerate(f, start=1):
                docs.append(
                    {
                        "source": txt_file.name,
                        "line": line_nr,
                        "text": line_text,
                    }
                )

    return docs


def search_logs_bm25_v1(
    application_id: str,
    query: str,
    limit: int = 20,
):
    docs = load_application_logs(application_id)
    if not docs:
        return [{"message": f"No logs found for: {application_id}"}]

    corpus = [doc["text"] for doc in docs]

    # Tokenize the corpus and only keep the ids (faster and saves memory):
    corpus_tokens = bm25s.tokenize(corpus, stopwords=None, stemmer=None)

    # Create the BM25 model and index the corpus:
    retriever = bm25s.BM25()
    retriever.index(corpus_tokens)
    ##### REMEMBER TO CACHE YOUR INDEX, OTHERWISE YOUR AGENT WILL REINDEX EVERY TIME IT IS CALLED. MFUCKER

    # Query the corpus, bm25s package automatically converts the query to lowercase:
    query_tokens = bm25s.tokenize(query, stopwords=None, stemmer=None)

    # We get back numpy arrys of size [n_queries, limit] ---> in the case of one query and default limit we get a 1x20 NumPy array.
    results, scores = retriever.retrieve(query_tokens, k=min(limit, len(docs)))

    matches = []
    for doc_idx, score in zip(results[0], scores[0]):
        if score > 0:
            matches.append(docs[doc_idx])

    if not matches:
        return [{"message": f"No matches found for query: {query}"}]

    return matches


if __name__ == "__main__":
    resulting_docs_list = search_logs_bm25(
        "application_1445062781478_0011", "Killing"
    )
