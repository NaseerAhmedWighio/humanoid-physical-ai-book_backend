import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from fastembed import TextEmbedding
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Initialize fastembed model with BGE small model (generates 384-dim vectors to match Qdrant collection)
embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

# Connect to Qdrant
qdrant_url = os.getenv("QDRANT_URL")
qdrant_api_key = os.getenv("QDRANT_API_KEY")
if qdrant_url and qdrant_url.startswith("https://"):
    # For HTTPS/secure connections
    qdrant = QdrantClient(
        url=qdrant_url,
        api_key=qdrant_api_key
    )
else:
    # For HTTP/insecure connections (local development)
    qdrant = QdrantClient(
        url=qdrant_url,
        api_key=qdrant_api_key,
        prefer_grpc=False
    )

def get_embedding(text):
    """Get embedding vector using fastembed (384-dim to match Qdrant collection)"""
    try:
        # Use fastembed (local) - generates 384-dim vectors to match Qdrant collection
        embeddings = list(embedding_model.embed([text]))
        return embeddings[0].tolist()  # Convert to list for serialization
    except Exception as e:
        logger.error(f"Error getting embedding: {e}")
        raise Exception(f"Embedding error: {str(e)}")

def retrieve(query, collection_name="humanoid_ai_book_new", limit=5):
    """Retrieve relevant chunks from Qdrant based on query"""
    try:
        embedding = get_embedding(query)

        # Use the query_points method which is the correct method for vector similarity search in newer versions
        result = qdrant.query_points(
            collection_name=collection_name,
            query=embedding,  # Pass the embedding vector
            limit=limit,
            with_payload=True
        )

        # Handle the result structure (Qdrant search returns ScoredPoint objects)
        texts = []
        for point in result.points:
            # Each point is a models.ScoredPoint object with id, payload, vector, and score
            if hasattr(point, 'payload') and 'text' in point.payload:
                texts.append({
                    "content": point.payload["text"],
                    "score": getattr(point, 'score', 1.0),
                    "metadata": point.payload.get("metadata", {})
                })
            elif hasattr(point, 'payload') and isinstance(point.payload, dict):
                # If payload has other content fields
                content = point.payload.get("content") or point.payload.get("text") or str(point.payload)
                texts.append({
                    "content": content,
                    "score": getattr(point, 'score', 1.0),
                    "metadata": point.payload
                })

        return texts
    except Exception as e:
        logger.error(f"Error in retrieval: {e}")

        # Return a helpful fallback message instead of raising an exception
        # This will allow the system to continue functioning even if RAG is temporarily unavailable
        logger.warning("Falling back to empty results due to retrieval error")
        return []  # Return empty list as fallback, which the calling code can handle gracefully