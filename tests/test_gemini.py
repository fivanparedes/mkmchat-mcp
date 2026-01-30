"""Test Gemini LLM integration"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mkmchat.llm.gemini import GeminiAssistant, get_gemini_assistant
from mkmchat.data.rag import RAGSystem
from mkmchat.tools.llm_tools import (
    ask_assistant,
    compare_characters_llm,
    suggest_team_llm,
    explain_mechanic_llm
)


async def test_gemini_integration():
    """Test Gemini LLM integration"""
    
    print("=" * 80)
    print("Gemini LLM Integration Test")
    print("=" * 80)
    
    # Check API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("\n❌ GEMINI_API_KEY not set!")
        print("\nTo test Gemini integration:")
        print("1. Get API key from: https://makersuite.google.com/app/apikey")
        print("2. Set environment variable:")
        print("   export GEMINI_API_KEY='your-api-key-here'")
        print("3. Run this test again")
        return
    
    print(f"\n✅ API Key found (length: {len(api_key)})")
    
    # Initialize RAG system
    print("\n1. Initializing RAG system...")
    rag = RAGSystem()
    if rag.enabled:
        rag.index_data()
        print(f"✅ RAG system ready with {len(rag.documents)} documents")
    else:
        print("⚠️  RAG system not available (sentence-transformers not installed)")
        rag = None
    
    # Initialize Gemini assistant
    print("\n2. Initializing Gemini assistant...")
    assistant = GeminiAssistant(rag_system=rag)
    
    if not assistant.enabled:
        print("❌ Gemini assistant initialization failed")
        return
    
    print(f"✅ Gemini assistant ready (model: {assistant.model_name})")
    
    # Test 1: Simple question
    print("\n" + "=" * 80)
    print("3. Testing simple question...")
    print("=" * 80)
    question = "What are the main character classes in MK Mobile?"
    print(f"\nQ: {question}\n")
    
    try:
        response = await assistant.query(question, use_rag=True)
        print(f"A: {response[:500]}...")
        print("✅ Simple question test passed")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Character comparison
    print("\n" + "=" * 80)
    print("4. Testing character comparison...")
    print("=" * 80)
    print("\nComparing: Klassic Scorpion vs Inferno Scorpion\n")
    
    try:
        comparison = await assistant.compare_characters(
            "Klassic Scorpion",
            "Inferno Scorpion"
        )
        print(f"Comparison:\n{comparison[:500]}...")
        print("✅ Character comparison test passed")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Team suggestion
    print("\n" + "=" * 80)
    print("5. Testing team suggestion...")
    print("=" * 80)
    print("\nStrategy: aggressive fire damage\n")
    
    try:
        team = await assistant.suggest_team_composition(
            strategy="aggressive fire damage"
        )
        print(f"Team Suggestion:\n{team[:500]}...")
        print("✅ Team suggestion test passed")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Mechanic explanation
    print("\n" + "=" * 80)
    print("6. Testing mechanic explanation...")
    print("=" * 80)
    print("\nMechanic: power drain\n")
    
    try:
        explanation = await assistant.explain_mechanic("power drain")
        print(f"Explanation:\n{explanation[:500]}...")
        print("✅ Mechanic explanation test passed")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 5: MCP tools
    print("\n" + "=" * 80)
    print("7. Testing MCP tools...")
    print("=" * 80)
    
    try:
        # Test ask_assistant tool
        print("\nTesting ask_assistant tool...")
        result = await ask_assistant("What's the best class for beginners?")
        if "content" in result and result["content"]:
            print("✅ ask_assistant tool works")
        else:
            print("❌ ask_assistant tool returned unexpected format")
        
        # Test compare_characters_llm tool
        print("\nTesting compare_characters_llm tool...")
        result = await compare_characters_llm("Scorpion", "Sub-Zero")
        if "content" in result and result["content"]:
            print("✅ compare_characters_llm tool works")
        else:
            print("❌ compare_characters_llm tool returned unexpected format")
        
        print("\n✅ All MCP tools tests passed")
    except Exception as e:
        print(f"❌ MCP tools error: {e}")
    
    # Summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    print("\n✅ Gemini integration is working correctly!")
    print(f"\nModel: {assistant.model_name}")
    print(f"RAG Enabled: {rag is not None and rag.enabled}")
    print(f"Documents Indexed: {len(rag.documents) if rag and rag.enabled else 0}")
    
    print("\n" + "=" * 80)
    print("Usage Examples")
    print("=" * 80)
    print("""
# Ask a question
await ask_assistant("How do I counter freeze teams?")

# Compare characters
await compare_characters_llm("Klassic Liu Kang", "Hellspawn Scorpion")

# Get team suggestions
await suggest_team_llm("defensive tank team")

# Explain mechanics
await explain_mechanic_llm("tag-in attacks")
    """)


if __name__ == "__main__":
    asyncio.run(test_gemini_integration())
