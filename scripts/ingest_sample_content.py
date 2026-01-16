#!/usr/bin/env python
"""
Script to ingest sample content into Qdrant for RAG functionality
"""
import os
import sys
from pathlib import Path
import requests
import time

# Add the backend directory to the path so we can import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

def check_qdrant_connection():
    """Check if Qdrant is accessible"""
    try:
        response = requests.get("http://localhost:6333/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def create_collection():
    """Create the Qdrant collection if it doesn't exist"""
    print("Creating Qdrant collection...")

    collection_config = {
        "vectors": {
            "size": 384,  # Size for BGE small model
            "distance": "Cosine"
        }
    }

    try:
        response = requests.put(
            "http://localhost:6333/collections/humanoid_ai_book_new",
            json=collection_config,
            timeout=10
        )

        if response.status_code == 200:
            print("Collection created successfully!")
            return True
        else:
            print(f"Failed to create collection: {response.status_code}, {response.text}")
            return False
    except Exception as e:
        print(f"Error creating collection: {e}")
        return False

def ingest_sample_content():
    """Ingest sample content into Qdrant"""
    print("Ingesting sample content into Qdrant...")

    # Sample content about ROS 2 and Humanoid Robotics
    sample_content = [
        {
            "id": 1,
            "payload": {
                "text": "ROS 2 (Robot Operating System 2) is a flexible framework for writing robot software. It provides a collection of tools, libraries, and conventions that aim to simplify the task of creating complex and robust robot behavior across a wide variety of robot platforms.",
                "metadata": {"source": "ROS2 Documentation", "section": "Introduction"}
            }
        },
        {
            "id": 2,
            "payload": {
                "text": "Humanoid robots are robots with physical features resembling the human body, typically having a head, torso, two arms, and two legs. They are designed to operate in human environments and interact with human tools and interfaces.",
                "metadata": {"source": "Humanoid Robotics Guide", "section": "Basics"}
            }
        },
        {
            "id": 3,
            "payload": {
                "text": "The Robot Operating System (ROS) provides libraries and tools to help software developers create robot applications. It includes hardware abstraction, device drivers, libraries, visualizers, message-passing, package management, and more.",
                "metadata": {"source": "ROS Documentation", "section": "Overview"}
            }
        },
        {
            "id": 4,
            "payload": {
                "text": "Qdrant is a vector similarity search engine that stores, indexes, and manages vectors with additional payload. It's used in RAG (Retrieval Augmented Generation) systems to retrieve relevant documents based on semantic similarity.",
                "metadata": {"source": "Vector Databases", "section": "RAG Systems"}
            }
        },
        {
            "id": 5,
            "payload": {
                "text": "Large Language Models (LLMs) are AI models trained on vast amounts of text data to understand and generate human-like text. They are used in RAG systems to generate responses based on retrieved context.",
                "metadata": {"source": "AI Models", "section": "LLM Fundamentals"}
            }
        }
    ]

    # Prepare points for insertion
    points = []
    for item in sample_content:
        # We'll need to generate embeddings for each text
        # For now, we'll skip this step and use a placeholder approach
        # In a real scenario, we would use the embedding service
        points.append({
            "id": item["id"],
            "payload": item["payload"]
        })

    # For now, let's just send the content to Qdrant
    # In the actual implementation, we need to generate embeddings
    try:
        # First, let's try to get the embedding service to generate vectors
        from src.services.retrieving import get_embedding

        # Generate embeddings for each content item
        upsert_data = []
        for i, item in enumerate(sample_content):
            try:
                embedding = get_embedding(item["payload"]["text"])
                upsert_data.append({
                    "id": item["id"],
                    "vector": embedding,
                    "payload": item["payload"]
                })
                print(f"Generated embedding for item {i+1}")
            except Exception as e:
                print(f"Error generating embedding for item {i+1}: {e}")
                continue

        if upsert_data:
            response = requests.put(
                "http://localhost:6333/collections/humanoid_ai_book_new/points?wait=true",
                json={"points": upsert_data},
                timeout=30
            )

            if response.status_code == 200:
                print(f"Successfully ingested {len(upsert_data)} content items into Qdrant!")
                return True
            else:
                print(f"Failed to ingest content: {response.status_code}, {response.text}")
                return False
        else:
            print("No embeddings were generated, so no content was ingested.")
            return False

    except Exception as e:
        print(f"Error ingesting content: {e}")
        return False

def main():
    print("📦 Ingesting Sample Content for RAG System")
    print("=" * 50)

    # Check if Qdrant is running
    if not check_qdrant_connection():
        print("❌ Qdrant is not running. Please start Qdrant first.")
        print("\nTo run Qdrant locally, you can:")
        print("1. Install Docker and run: docker run -d --name qdrant -p 6333:6333 qdrant/qdrant")
        print("2. Or download from: https://qdrant.tech/documentation/quick-start/")
        print("3. Or use the cloud version: https://cloud.qdrant.io/")
        return False

    print("✅ Qdrant is accessible")

    # Try to create collection
    collection_created = create_collection()
    if not collection_created:
        print("⚠️  Could not create collection. It might already exist.")
        # Continue anyway, as it might already exist

    # Ingest sample content
    success = ingest_sample_content()

    if success:
        print("\n🎉 Sample content ingested successfully!")
        print("The RAG system is now ready to use with sample content.")
        return True
    else:
        print("\n❌ Content ingestion failed.")
        return False

if __name__ == "__main__":
    main()