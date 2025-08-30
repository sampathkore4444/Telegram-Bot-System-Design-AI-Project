#!/usr/bin/env python3
import requests
import time
import os


def check_ollama():
    """Check if Ollama is running"""
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    max_retries = 10

    for i in range(max_retries):
        try:
            response = requests.get(f"{host}/api/tags", timeout=5)
            if response.status_code == 200:
                print("✅ Ollama is running!")
                return True
            print(f"Ollama responded with status: {response.status_code}")
        except Exception as e:
            print(f"Attempt {i+1}/{max_retries}: Ollama not ready - {e}")
        time.sleep(5)

    print("❌ Ollama failed to start")
    return False


if __name__ == "__main__":
    check_ollama()
