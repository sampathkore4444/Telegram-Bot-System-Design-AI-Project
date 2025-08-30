#!/bin/bash

# Set Ollama to listen on all interfaces
export OLLAMA_HOST=0.0.0.0:11434

echo "🔧 Setting up Ollama..."

# Start Ollama server in background
echo "🚀 Starting Ollama server..."
ollama serve &

# Give it time to start
echo "⏳ Waiting for Ollama to initialize..."
sleep 20

# Check if Ollama is responsive
if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "✅ Ollama server is running"
else
    echo "❌ Ollama server not responding"
    echo "Debug: Checking processes..."
    ps aux | grep ollama
    echo "Trying to continue anyway..."
fi

# Pull the model
echo "📦 Downloading phi3:3.8b model..."
ollama pull phi3:3.8b

echo "🤖 Starting Telegram bot..."
python bot.py