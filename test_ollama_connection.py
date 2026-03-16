#!/usr/bin/env python3
"""Test Ollama connection and list available models."""

import requests
import json

OLLAMA_BASE_URL = "http://localhost:11434"

def check_ollama():
    """Check if Ollama is running and list models."""
    try:
        print("Attempting to connect to Ollama at", OLLAMA_BASE_URL)
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        
        if response.status_code == 200:
            models = response.json().get("models", [])
            print("\n✓ Successfully connected to Ollama!")
            print(f"\nAvailable models ({len(models)}):")
            for model in models:
                print(f"  - {model.get('name', 'Unknown')}")
            return True
        else:
            print(f"✗ Ollama responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to Ollama. Make sure it's running:")
        print("  ollama serve")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    check_ollama()
