#!/usr/bin/env python3
import requests
import time
import os


def test_connection():
    """Test Ollama connection"""
    hosts = ["http://localhost:11434", "http://127.0.0.1:11434"]

    for host in hosts:
        try:
            print(f"Testing connection to {host}...")
            response = requests.get(f"{host}/api/tags", timeout=10)
            print(f"✅ Success! Status: {response.status_code}")
            return True
        except Exception as e:
            print(f"❌ Failed: {e}")

    return False


if __name__ == "__main__":
    print("Testing Ollama connection...")
    if test_connection():
        print("Ollama is running! 🎉")
    else:
        print("Ollama is not running 😞")
