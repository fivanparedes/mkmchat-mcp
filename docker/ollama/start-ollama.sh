#!/bin/sh
set -eu

MODEL="${OLLAMA_MODEL:-llama3.2:3b}"

/bin/ollama serve &
OLLAMA_PID="$!"

cleanup() {
  kill "$OLLAMA_PID" 2>/dev/null || true
}
trap cleanup INT TERM

for _ in $(seq 1 60); do
  if /bin/ollama list >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

echo "Ensuring Ollama model is available: ${MODEL}"
/bin/ollama pull "$MODEL"

wait "$OLLAMA_PID"
