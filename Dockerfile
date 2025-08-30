FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Download and install Ollama
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Verify Ollama installation
RUN which ollama && ollama --version

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY bot.py .
COPY start.sh .

# Make start script executable
RUN chmod +x start.sh

EXPOSE 11434

# Use the start script
CMD ["./start.sh"]