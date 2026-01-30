"""Test Ollama integration"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from mkmchat.llm.ollama import OllamaAssistant, get_ollama_assistant
from mkmchat.data.rag import RAGSystem


async def test_ollama_basic():
    """Test basic Ollama functionality"""
    print("=== Testing Ollama Basic Functionality ===\n")
    
    assistant = OllamaAssistant()
    
    if not assistant.enabled:
        print("❌ Ollama not available. Please run: ./setup_ollama.sh")
        return False
    
    print(f"✅ Ollama connected: {assistant.base_url}")
    print(f"✅ Model: {assistant.model_name}\n")
    
    # Test simple query without RAG
    print("Testing simple query (no RAG)...")
    response = await assistant.query(
        "What is Mortal Kombat Mobile?",
        use_rag=False
    )
    print(f"Response: {response[:200]}...\n")
    
    return True


async def test_ollama_with_rag():
    """Test Ollama with RAG system"""
    print("=== Testing Ollama with RAG ===\n")
    
    # Initialize RAG
    rag = RAGSystem()
    if not rag.enabled:
        print("⚠️  RAG system not available, skipping RAG test")
        return True
    
    assistant = get_ollama_assistant(rag_system=rag)
    
    if not assistant.enabled:
        print("❌ Ollama not available")
        return False
    
    # Test character query with RAG
    print("Testing character query with RAG context...")
    response = await assistant.query(
        "Tell me about Scorpion's abilities",
        use_rag=True
    )
    print(f"Response: {response[:300]}...\n")
    
    return True


async def test_compare_characters():
    """Test character comparison"""
    print("=== Testing Character Comparison ===\n")
    
    rag = RAGSystem()
    assistant = get_ollama_assistant(rag_system=rag)
    
    if not assistant.enabled:
        print("❌ Ollama not available")
        return False
    
    print("Comparing Scorpion vs Sub-Zero...")
    response = await assistant.compare_characters("Scorpion", "Sub-Zero")
    print(f"Response: {response[:400]}...\n")
    
    return True


async def test_team_suggestion():
    """Test team composition suggestion"""
    print("=== Testing Team Suggestion ===\n")
    
    rag = RAGSystem()
    assistant = get_ollama_assistant(rag_system=rag)
    
    if not assistant.enabled:
        print("❌ Ollama not available")
        return False
    
    print("Suggesting team for 'high damage' strategy...")
    response = await assistant.suggest_team_composition("high damage")
    print(f"Response: {response[:400]}...\n")
    
    return True


async def test_explain_mechanic():
    """Test mechanic explanation"""
    print("=== Testing Mechanic Explanation ===\n")
    
    rag = RAGSystem()
    assistant = get_ollama_assistant(rag_system=rag)
    
    if not assistant.enabled:
        print("❌ Ollama not available")
        return False
    
    print("Explaining 'power drain' mechanic...")
    response = await assistant.explain_mechanic("power drain")
    print(f"Response: {response[:400]}...\n")
    
    return True


async def main():
    """Run all tests"""
    print("=" * 60)
    print("MKMChat - Ollama Integration Test Suite")
    print("=" * 60)
    print()
    
    tests = [
        ("Basic Functionality", test_ollama_basic),
        ("RAG Integration", test_ollama_with_rag),
        ("Character Comparison", test_compare_characters),
        ("Team Suggestion", test_team_suggestion),
        ("Mechanic Explanation", test_explain_mechanic),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Error in {name}: {e}\n")
            results.append((name, False))
    
    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print()
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    asyncio.run(main())
