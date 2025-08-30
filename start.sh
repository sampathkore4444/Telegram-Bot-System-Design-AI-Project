#!/bin/bash

# Set Ollama environment variables
export OLLAMA_HOST="0.0.0.0:11434"
export OLLAMA_NUM_PARALLEL=1

echo "🚀 Starting Ollama server..."

# Start Ollama in the background with explicit host binding
ollama serve --host $OLLAMA_HOST &

# Wait for Ollama to start
echo "⏳ Waiting for Ollama to start..."
sleep 15

# Check if Ollama is running
if curl -f http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama server is running"
else
    echo "❌ Ollama server failed to start"
    exit 1
fi

echo "📦 Pulling model: deepseek-r1:8b..."
ollama pull deepseek-r1:8b

if [ $? -eq 0 ]; then
    echo "✅ Model pulled successfully"
else
    echo "❌ Model pull failed"
    exit 1
fi

# Wait a bit more for model to be fully loaded
sleep 10

echo "🤖 Starting Telegram bot..."
python bot.py