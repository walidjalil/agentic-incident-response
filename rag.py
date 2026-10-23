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

RAG_DOCS_DIR = Path(__file__).parent / "rag_docs"

model = None

all_chunks_cache = None
document_embeddings_cache = None


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


def get_embedding_model():
    global model

    if model is None:
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    return model


def build_rag_index():
    global all_chunks_cache
    global document_embeddings_cache

    if all_chunks_cache is not None and document_embeddings_cache is not None:
        return

    docs = []
    for txt_file in RAG_DOCS_DIR.glob("*.md"):
        with open(txt_file) as f:
            docs.append(
                {
                    "source": txt_file.name,
                    "text": f.read(),
                }
            )

    all_chunks = []
    for doc in docs:
        all_chunks.extend(get_overlapped_chunks(doc, 200, 50))

    model = get_embedding_model()

    chunk_texts = [chunk["text"] for chunk in all_chunks]
    document_embeddings = model.encode_document(chunk_texts)

    all_chunks_cache = all_chunks
    document_embeddings_cache = document_embeddings


def retrieve(query, top_k=3):
    build_rag_index()

    model = get_embedding_model()
    query_embedding = model.encode_query(query)

    results = []
    for i in range(len(all_chunks_cache)):
        cosine = np.dot(query_embedding, document_embeddings_cache[i, :]) / (
            np.linalg.norm(query_embedding)
            * np.linalg.norm(document_embeddings_cache[i, :])
        )

        results.append(
            {
                "chunk_id": i,
                "source": all_chunks_cache[i]["source"],
                "text": all_chunks_cache[i]["text"],
                "score": float(cosine),
            }
        )

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def print_top_ranked_chunks(top_k, results):
    for i in range(top_k):
        print(f"\nRank {i + 1}")
        print("Source:", results[i]["source"])
        print("Score:", results[i]["score"])
        print("Text:", results[i]["text"])


def main():
    # ---------------- Retrieval Stage -------------------------------------------

    query = "What should I investigate when the database reaches its maximum connection limit?"
    top_k = 3

    results = retrieve(query, top_k)

    # ---------------------- Augmentation Stage --------------------------------

    context_list = []

    for i in range(len(results)):
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


if __name__ == "__main__":
    main()
