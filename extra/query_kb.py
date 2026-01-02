"""
query_kb.py

Test querying the HNU knowledge base built with generate_knowledge_base.py.
Loads FAISS index + metadata.jsonl, embeds your query, and retrieves top-k results.
"""

import os
import json
import argparse
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

def load_metadata(meta_path: str):
    metadata = []
    with open(meta_path, 'r', encoding='utf-8') as f:
        for line in f:
            metadata.append(json.loads(line.strip()))
    return metadata

def query_kb(query: str, faiss_index: str, metadata_path: str, model_name: str = 'all-MiniLM-L6-v2', top_k: int = 5):
    # Load FAISS index
    index = faiss.read_index(faiss_index)

    # Load metadata
    metadata = load_metadata(metadata_path)

    # Load embedding model
    model = SentenceTransformer(model_name)

    # Compute embedding for query
    query_emb = model.encode([query], convert_to_numpy=True)
    faiss.normalize_L2(query_emb)

    # Search
    scores, indices = index.search(query_emb, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or idx >= len(metadata):
            continue
        item = metadata[idx]
        results.append({
            "text": item["text"],
            "source": item["source"],
            "score": float(score)
        })
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--kb_dir", type=str, default="./kb", help="Knowledge base folder")
    parser.add_argument("--model", type=str, default="all-MiniLM-L6-v2", help="SentenceTransformer model name")
    parser.add_argument("--top_k", type=int, default=5, help="Number of results to return")
    args = parser.parse_args()

    faiss_index = os.path.join(args.kb_dir, "faiss_index.bin")
    metadata_path = os.path.join(args.kb_dir, "metadata.jsonl")

    if not os.path.exists(faiss_index) or not os.path.exists(metadata_path):
        print("❌ Could not find knowledge base files. Run generate_knowledge_base.py first.")
        return

    print("✅ Knowledge base loaded. Type your queries (English or German). Type 'exit' to quit.\n")

    while True:
        query = input("🔎 Query: ").strip()
        if query.lower() in ["exit", "quit"]:
            break
        results = query_kb(query, faiss_index, metadata_path, args.model, args.top_k)
        print("\n--- Top Results ---")
        for i, r in enumerate(results, 1):
            print(f"[{i}] (score={r['score']:.4f}) source={r['source']}")
            print(f"     {r['text'][:300]}...\n")


if __name__ == "__main__":
    main()
