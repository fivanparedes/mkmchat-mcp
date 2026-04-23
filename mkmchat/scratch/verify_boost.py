
import sys
import os
from pathlib import Path

# Add the project root to sys.path
sys.path.append(os.getcwd())

from mkmchat.data.rag import RAGSystem

rag = RAGSystem()
rag.index_data()

print("--- Searching for: Shao Kahn's brutality set ---")
results = rag.search_equipment("Shao Kahn's brutality set", top_k=5)

for i, (doc, score) in enumerate(results, 1):
    print(f"{i}. {doc.metadata.get('name')} (Score: {score:.3f})")
    print(f"   Content: {doc.content[:150]}...")
    print("-" * 20)

print("\n--- Searching for: Horde Chef's Paraphernalia ---")
results = rag.search_equipment("Horde Chef's Paraphernalia", top_k=5)

for i, (doc, score) in enumerate(results, 1):
    print(f"{i}. {doc.metadata.get('name')} (Score: {score:.3f})")
