#!/bin/bash

# Start Ollama in background
ollama serve &

# Wait for Ollama to start
sleep 5

# Pull the model (using a smaller model for Railway free tier)
ollama pull gemma:2b &

# Wait for model pull to complete
wait

# Start the bot
python bot.py