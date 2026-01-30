#!/bin/bash
# Setup script for Ollama local LLM integration

set -e

echo "=== Ollama Setup for MKMChat ==="
echo ""

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama not found. Installing..."
    echo ""
    curl -fsSL https://ollama.com/install.sh | sh
    echo ""
    echo "✅ Ollama installed successfully"
else
    echo "✅ Ollama is already installed"
fi

echo ""
echo "=== Starting Ollama Service ==="
# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "Starting Ollama service in background..."
    nohup ollama serve > /tmp/ollama.log 2>&1 &
    sleep 2
    echo "✅ Ollama service started"
else
    echo "✅ Ollama service is already running"
fi

echo ""
echo "=== Pulling Llama 3.2 3B Model ==="
if ollama list | grep -q "llama3.2:3b"; then
    echo "✅ llama3.2:3b is already available"
else
    echo "Pulling llama3.2:3b model (this may take a few minutes)..."
    ollama pull llama3.2:3b
    echo "✅ Model downloaded successfully"
fi

echo ""
echo "=== Installing Python Dependencies ==="
pip install httpx

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "Available models:"
ollama list
echo ""
echo "You can now use Ollama tools in mkmchat:"
echo "  - ask_ollama"
echo "  - compare_characters_ollama"
echo "  - suggest_team_ollama"
echo "  - explain_mechanic_ollama"
echo ""
echo "To test Ollama manually:"
echo "  ollama run llama3.2:3b"
echo ""
echo "To stop Ollama service:"
echo "  pkill ollama"
