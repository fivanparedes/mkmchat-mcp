"""Test script for RAG system"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mkmchat.tools.semantic_search import get_rag_system, semantic_search, search_by_strategy, explain_mechanic


async def test_rag_system():
    """Test RAG system functionality"""
    
    print("=" * 80)
    print("RAG System Test")
    print("=" * 80)
    
    # Initialize RAG system
    print("\n1. Initializing RAG system...")
    rag = get_rag_system()
    
    if not rag.enabled:
        print("❌ RAG system not available. Install dependencies:")
        print("   pip install sentence-transformers")
        return
    
    print(f"✅ RAG system initialized with {len(rag.documents)} documents")
    
    # Test 1: Semantic search for characters
    print("\n" + "=" * 80)
    print("2. Testing semantic search for 'fire damage characters'...")
    print("=" * 80)
    results = await semantic_search(
        query="characters with fire attacks and high damage",
        top_k=5,
        doc_type="character"
    )
    
    for i, result in enumerate(results, 1):
        if "error" in result or "message" in result:
            print(f"\n{result}")
        else:
            print(f"\n{i}. {result.get('metadata', {}).get('name', 'Unknown')}")
            print(f"   Type: {result['type']}")
            print(f"   Score: {result['similarity_score']}")
            print(f"   Preview: {result['content'][:200]}...")
    
    # Test 2: Search by strategy
    print("\n" + "=" * 80)
    print("3. Testing search by strategy: 'high damage dealer'...")
    print("=" * 80)
    results = await search_by_strategy(strategy="high damage dealer", top_k=3)
    
    for result in results:
        if "error" in result:
            print(f"\n{result}")
        else:
            print(f"\nStrategy: {result.get('strategy')}")
            print(f"\nTop Characters:")
            for char in result.get('characters', [])[:3]:
                print(f"  - {char['name']} ({char['class']}) - Score: {char['relevance_score']}")
            
            print(f"\nRelevant Equipment:")
            for equip in result.get('equipment', [])[:3]:
                print(f"  - {equip['name']} ({equip['type']}) - Score: {equip['relevance_score']}")
    
    # Test 3: Explain mechanic
    print("\n" + "=" * 80)
    print("4. Testing explain mechanic: 'What is power drain?'...")
    print("=" * 80)
    results = await explain_mechanic(mechanic_query="How does power drain work in combat?")
    
    for result in results:
        if "error" in result or "message" in result:
            print(f"\n{result}")
        else:
            print(f"\nQuery: {result.get('query')}")
            
            if result.get('gameplay_mechanics'):
                print("\nGameplay Mechanics:")
                for mech in result['gameplay_mechanics']:
                    print(f"  Score: {mech['relevance_score']}")
                    print(f"  {mech['content'][:300]}...")
            
            if result.get('glossary_terms'):
                print("\nGlossary Terms:")
                for term in result['glossary_terms']:
                    print(f"  Score: {term['relevance_score']}")
                    print(f"  {term['content'][:200]}...")
    
    # Test 4: General semantic search
    print("\n" + "=" * 80)
    print("5. Testing general search: 'equipment that increases critical hits'...")
    print("=" * 80)
    results = await semantic_search(
        query="equipment that increases critical hit chance",
        top_k=5,
        doc_type="equipment"
    )
    
    for i, result in enumerate(results, 1):
        if "error" in result or "message" in result:
            print(f"\n{result}")
        else:
            print(f"\n{i}. {result.get('metadata', {}).get('name', 'Unknown')}")
            print(f"   Score: {result['similarity_score']}")
            print(f"   {result['content'][:250]}...")
    
    print("\n" + "=" * 80)
    print("✅ RAG system tests completed!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_rag_system())
