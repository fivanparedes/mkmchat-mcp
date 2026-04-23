import asyncio
import os
import sys

# Add /app to sys.path so we can import mkmchat
sys.path.append("/app")

from mkmchat.tools.semantic_search import get_rag_system
from mkmchat.http_server import _retrieve_equipment_items

async def main():
    rag = get_rag_system()
    if not rag.enabled:
        print("RAG not enabled")
        return

    query = "Shao Kahn brutality gear"
    print(f"Testing query: {query}")
    
    results = _retrieve_equipment_items(
        rag,
        query,
        top_k_per_variant=15,
        top_k_final=10,
        min_similarity=0.22
    )
    
    print(f"\nFound {len(results)} results:")
    for doc, score in results:
        name = doc.metadata.get("name")
        tier = doc.metadata.get("tier")
        print(f"- (rel={score:.2f}) [{tier}] {name}")

if __name__ == "__main__":
    asyncio.run(main())
