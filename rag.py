#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 22 01:10:56 2026

@author: walidajalil
"""

from sentence_transformers import SentenceTransformer
from pathlib import Path
import numpy as np
import agent
import utils


# ---------------- Retrieval Stage -------------------------------------------
def get_overlapped_chunks(textin, chunksize, overlapsize):
    source = textin["source"]
    text = textin["text"]
    words = text.split()
    list_of_chunks = []
    chunks = [
        words[a : a + chunksize]
        for a in range(0, len(words), chunksize - overlapsize)
    ]
    for i in range(len(chunks)):
        dict_of_chunks = {"source": source, "text": " ".join(chunks[i])}
        list_of_chunks.append(dict_of_chunks)

    return list_of_chunks


docs = []
for txt_file in Path("rag_docs").glob("*.md"):
    print(txt_file)
    with open(txt_file) as f:
        lines = f.read()
        # Save file name and file text in dicts.
        docs.append({"source": txt_file.name, "text": lines})

all_chunks = []
for doc in docs:
    list_of_chunks = get_overlapped_chunks(doc, 200, 50)
    all_chunks.extend(list_of_chunks)


model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

query = "What should I investigate when the database reaches its maximum connection limit?"

# Embedd your query string and document strings. Each string outputs a d dimensional vector.
chunk_texts = [chunk["text"] for chunk in all_chunks]
document_embeddings = model.encode_document(chunk_texts)
query_embedding = model.encode_query(query)

results = []
for i in range(len(chunk_texts)):
    cosine = np.dot(query_embedding, document_embeddings[i, :]) / (
        np.linalg.norm(query_embedding)
        * np.linalg.norm(document_embeddings[i, :])
    )

    results.append(
        {
            "chunk_id": i,
            "source": all_chunks[i]["source"],
            "text": all_chunks[i]["text"],
            "score": cosine,
        }
    )

results.sort(key=lambda x: x["score"], reverse=True)

top_k = 3


def print_top_ranked_chunks(top_k, results):
    for i in range(top_k):
        print(f"\nRank {i + 1}")
        print("Source:", results[i]["source"])
        print("Score:", results[i]["score"])
        print("Text:", results[i]["text"])


# ---------------------- Augmentation Stage --------------------------------

context_list = []
top_k_chunks = results[:top_k]

for i in range(top_k):
    source_string = f"[Source: {results[i]['source']}]"
    text = source_string + "\n" + results[i]["text"]
    context_list.append(text)

llm_retrieval_context = "\n\n".join(context_list)


rag_prompt = f"""
Use the retrieved context below to answer the question.

Retrieved Context:
{llm_retrieval_context}

Question:
{query}
"""

# ------------------------- Generation Stage --------------------------------


messages = [
    {
        "role": "user",
        "content": rag_prompt,
    }
]

answer = agent.ask_llm(messages)
print(utils.remove_thinking(answer["content"]))
