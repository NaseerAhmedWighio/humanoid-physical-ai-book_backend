#!/usr/bin/env python
"""
Script to set up Qdrant vector database for RAG functionality
"""
import os
import subprocess
import sys
import time
import requests
from pathlib import Path

def check_qdrant_running():
    """Check if Qdrant is already running"""
    try:
        response = requests.get("http://localhost:6333/dashboard", timeout=5)
        return response.status_code == 200
    except:
        return False

def install_and_run_qdrant():
    """Install and run Qdrant using Docker"""
    print("Setting up Qdrant Vector Database...")

    # Check if Docker is installed
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            print("- Docker is not installed or not accessible.")
            print("Please install Docker Desktop and make sure it's running.")
            return False
        print("+ Docker is installed")
    except FileNotFoundError:
        print("- Docker is not installed or not in PATH.")
        print("Please install Docker Desktop from https://www.docker.com/products/docker-desktop")
        return False

    # Check if Qdrant container is already running
    result = subprocess.run(["docker", "ps"], capture_output=True, text=True)
    if "qdrant" in result.stdout:
        print("+ Qdrant container is already running")
        return True

    # Check if Qdrant image exists locally
    result = subprocess.run(["docker", "images"], capture_output=True, text=True)
    if "qdrant/qdrant" not in result.stdout:
        print("Pulling Qdrant Docker image...")
        pull_result = subprocess.run(["docker", "pull", "qdrant/qdrant"], capture_output=True, text=True)
        if pull_result.returncode != 0:
            print("- Failed to pull Qdrant image")
            print(pull_result.stderr)
            return False
        print("+ Qdrant image pulled successfully")

    # Run Qdrant container
    print("Starting Qdrant container...")
    run_cmd = [
        "docker", "run", "-d",
        "--name", "qdrant-humanoid-ai",
        "-p", "6333:6333",
        "-p", "6334:6334",
        "qdrant/qdrant"
    ]

    run_result = subprocess.run(run_cmd, capture_output=True, text=True)
    if run_result.returncode != 0:
        print("- Failed to start Qdrant container")
        print(run_result.stderr)
        return False

    print("+ Qdrant container started successfully")
    print("Waiting for Qdrant to be ready...")

    # Wait for Qdrant to be ready
    for i in range(30):  # Wait up to 30 seconds
        if check_qdrant_running():
            print("Qdrant is ready and accessible!")
            return True
        time.sleep(1)
        if i % 5 == 0:  # Print status every 5 seconds
            print(f"   Still waiting... ({i+1}/30 seconds)")

    print("- Qdrant failed to start properly")
    return False

def create_env_file():
    """Create a proper .env file with default configurations"""
    env_content = """# Environment Variables for Humanoid AI Book Backend

# OpenRouter API Key for LLM access (get from https://openrouter.ai/)
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Qdrant Vector Database Configuration
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=

# LLM Provider Configuration
LLM_PROVIDER=gemini
OPENROUTER_MODEL=mistralai/devstral-2512:free
TRANSLATION_MODEL=google/gemma-3-4b-it:free

# Database Configuration
DATABASE_URL=sqlite:///./humanoid_ai_book.db
NEON_DATABASE_URL=

# Authentication Configuration
JWT_SECRET=your_jwt_secret_here_change_this_in_production
BETTER_AUTH_URL=http://localhost:3000
BETTER_AUTH_SECRET=your_better_auth_secret_here

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000,http://127.0.0.1:8000
"""

    env_path = Path("./.env")  # Create in current directory (which is backend)
    if not env_path.exists():
        with open(env_path, "w") as f:
            f.write(env_content)
        print("Created .env file with default configurations")
        print("Remember to update OPENROUTER_API_KEY with your actual API key!")
    else:
        print(".env file already exists")

def main():
    print("Qdrant Setup for Humanoid AI Book")
    print("=" * 50)

    # Create environment file
    create_env_file()

    # Check if Qdrant is already running
    if check_qdrant_running():
        print("+ Qdrant is already running and accessible!")
        print("http://localhost:6333 - REST API")
        print("http://localhost:6333/dashboard - Web UI")
        return True

    print("? Qdrant is not running. Attempting to start...")

    # Try to install and run Qdrant
    success = install_and_run_qdrant()

    if success:
        print("\nQdrant setup completed successfully!")
        print("\nQdrant is now running:")
        print("   • API: http://localhost:6333")
        print("   • Dashboard: http://localhost:6333/dashboard")
        print("   • Health check: http://localhost:6333/health")
        print("\nTo stop Qdrant: docker stop qdrant-humanoid-ai")
        print("To restart Qdrant: docker start qdrant-humanoid-ai")
        print("To remove Qdrant container: docker rm qdrant-humanoid-ai")
        return True
    else:
        print("\nQdrant setup failed.")
        print("\nAlternative installation methods:")
        print("1. Manual Docker: docker run -d --name qdrant -p 6333:6333 qdrant/qdrant")
        print("2. Download from: https://qdrant.tech/documentation/quick-start/")
        print("3. Use cloud version: https://cloud.qdrant.io/")
        return False

if __name__ == "__main__":
    main()