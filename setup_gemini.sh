#!/bin/bash

# Setup script for Gemini LLM integration

echo "=============================================="
echo "Gemini LLM Integration Setup"
echo "=============================================="
echo ""

# Check if virtual environment is active
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  No virtual environment detected."
    echo "Activating virtual environment..."
    if [[ -f "venv/bin/activate" ]]; then
        source venv/bin/activate
    else
        echo "❌ Virtual environment not found at venv/"
        echo "Please create one first: python -m venv venv"
        exit 1
    fi
fi

echo "✅ Virtual environment: $VIRTUAL_ENV"
echo ""

# Install google-generativeai
echo "1. Installing google-generativeai..."
pip install google-generativeai >/dev/null 2>&1

if [[ $? -eq 0 ]]; then
    echo "✅ google-generativeai installed"
else
    echo "❌ Failed to install google-generativeai"
    exit 1
fi

echo ""

# Check for API key
if [[ -z "$GEMINI_API_KEY" ]]; then
    echo "2. Setting up API key..."
    echo ""
    echo "📋 Get your Gemini API key from:"
    echo "   https://makersuite.google.com/app/apikey"
    echo ""
    echo "Then set the environment variable:"
    echo "   export GEMINI_API_KEY='your-api-key-here'"
    echo ""
    echo "⚠️  API key not set yet. Please set it before testing."
else
    echo "2. API Key Status"
    echo "✅ GEMINI_API_KEY is set (length: ${#GEMINI_API_KEY})"
fi

echo ""
echo "=============================================="
echo "Setup Complete!"
echo "=============================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Set your API key (if not done):"
echo "   export GEMINI_API_KEY='your-api-key-here'"
echo ""
echo "2. Test the integration:"
echo "   python tests/test_gemini.py"
echo ""
echo "3. Start the MCP server:"
echo "   python -m mkmchat"
echo ""
echo "Available LLM tools:"
echo "  • ask_assistant - Ask any question about the game"
echo "  • compare_characters_llm - Compare two characters with AI"
echo "  • suggest_team_llm - Get AI-powered team suggestions"
echo "  • explain_mechanic_llm - Get detailed mechanic explanations"
echo ""
