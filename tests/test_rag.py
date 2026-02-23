"""Test script for RAG system"""

import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mkmchat.tools.semantic_search import (
    get_rag_system,
    semantic_search,
    search_characters_advanced,
    search_equipment_advanced,
)


def _print_mcp_result(result: dict) -> None:
    """Pretty-print an MCP-style tool result dict."""
    for block in result.get("content", []):
        print(block.get("text", ""))


async def test_rag_system():
    """Test RAG system functionality"""

    print("=" * 80)
    print("RAG System Test")
    print("=" * 80)

    # ---- 1. Initialise RAG system ----
    print("\n1. Initializing RAG system...")
    rag = get_rag_system()

    if not rag.enabled:
        print("❌ RAG system not available. Install dependencies:")
        print("   pip install sentence-transformers")
        return

    print(f"✅ RAG system initialized with {len(rag.documents)} documents")

    # ---- 2. RAG status / health ----
    print("\n" + "=" * 80)
    print("2. RAG system status")
    print("=" * 80)
    status = rag.get_status()
    for key, value in status.items():
        print(f"   {key}: {value}")

    # ---- 3. Semantic search – characters ----
    print("\n" + "=" * 80)
    print("3. Semantic search: 'characters with fire attacks and high damage'")
    print("=" * 80)
    result = await semantic_search(
        query="characters with fire attacks and high damage",
        top_k=5,
        doc_type="character",
    )
    _print_mcp_result(result)

    # ---- 4. Advanced character search ----
    print("\n" + "=" * 80)
    print("4. Advanced character search: keyword='fire'")
    print("=" * 80)
    result = await search_characters_advanced(keyword="fire")
    _print_mcp_result(result)

    # ---- 5. Semantic search – equipment ----
    print("\n" + "=" * 80)
    print("5. Semantic search: 'equipment that increases critical hit chance'")
    print("=" * 80)
    result = await semantic_search(
        query="equipment that increases critical hit chance",
        top_k=5,
        doc_type="equipment",
    )
    _print_mcp_result(result)

    # ---- 6. Advanced equipment search ----
    print("\n" + "=" * 80)
    print("6. Advanced equipment search: keyword='power', equip_type='Weapon'")
    print("=" * 80)
    result = await search_equipment_advanced(keyword="power", equip_type="Weapon")
    _print_mcp_result(result)

    # ---- 7. Cache invalidation check ----
    print("\n" + "=" * 80)
    print("7. Cache staleness check")
    print("=" * 80)
    stale = rag.is_stale()
    print(f"   Data stale: {stale}")
    rebuilt = rag.check_and_reindex()
    print(f"   Reindex triggered: {rebuilt}")

    print("\n" + "=" * 80)
    print("✅ RAG system tests completed!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_rag_system())
