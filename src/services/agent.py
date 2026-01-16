import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from openai import OpenAI
from typing import List, Dict, Any
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from ..database import get_db_with_retry
from ..models.chat_session import ChatSession
from ..models.chat_message import ChatMessage
import time

load_dotenv()

logger = logging.getLogger(__name__)

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

# Initialize OpenAI client for Gemini
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
if not openrouter_api_key:
    raise ValueError("OPENROUTER_API_KEY environment variable is required")

client = OpenAI(
    api_key=openrouter_api_key,
    base_url="https://openrouter.ai/api/v1/"
)

# In-memory storage for conversation context (in production, use a proper database)
# This is kept for fallback purposes
conversation_contexts = {}

# In-memory session locks to prevent concurrent requests for the same session
session_locks = {}
import threading

def get_embedding(text):
    """Get embedding vector using the retrieving service to ensure consistency"""
    try:
        # Use the same embedding model as the retrieving service to ensure consistency
        from .retrieving import get_embedding as retrieving_get_embedding
        return retrieving_get_embedding(text)
    except Exception as e:
        logger.error(f"Error getting embedding in agent: {e}")
        raise Exception(f"Embedding error: {str(e)}")

def retrieve(query: str, limit: int = 5) -> List[str]:
    """Retrieve relevant chunks from Qdrant based on query"""
    try:
        from .retrieving import retrieve as retrieving_retrieve
        # Use the main retrieve function from retrieving service to ensure consistency
        result = retrieving_retrieve(query, collection_name="humanoid_ai_book_new", limit=limit)
        # Ensure we return a list of strings or dictionaries
        if result is None:
            return []
        return result
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in agent retrieval: {e}")
        return []

def get_conversation_context(session_id: str) -> List[Dict[str, str]]:
    """Get conversation history for a session with fallback to in-memory storage"""
    # Try to get from database first
    db_context = get_conversation_context_from_db(session_id)
    if db_context and len(db_context) > 0:
        return db_context
    # Fallback to in-memory storage
    if session_id not in conversation_contexts:
        conversation_contexts[session_id] = []
    return conversation_contexts[session_id]

def get_conversation_context_from_db(session_id: str) -> List[Dict[str, str]]:
    """Get conversation history for a session from database with retry logic"""
    for attempt in range(3):  # Try up to 3 times
        try:
            db = get_db_with_retry()
            # Convert session_id to UUID format if needed
            from uuid import UUID
            try:
                uuid_session_id = UUID(session_id)
            except ValueError:
                # If it's not a valid UUID, return empty list (session doesn't exist in DB)
                return []

            messages = db.query(ChatMessage).filter(
                ChatMessage.session_id == uuid_session_id
            ).order_by(ChatMessage.created_at).all()

            # Convert to the expected format
            conversation_history = []
            for msg in messages:
                conversation_history.append({
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.created_at.isoformat() if msg.created_at else None
                })

            return conversation_history
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} to get conversation context from DB failed: {e}")
            if attempt == 2:  # Last attempt
                # Fallback to in-memory storage
                logger.warning("Falling back to in-memory storage for conversation context")
                if session_id not in conversation_contexts:
                    conversation_contexts[session_id] = []
                return conversation_contexts[session_id]
            time.sleep(0.1 * (2 ** attempt))  # Exponential backoff
        finally:
            try:
                db.close()
            except:
                pass


def add_message_to_context_in_db(session_id: str, role: str, content: str, sources: List[Dict[str, Any]] = None):
    """Add a message to the conversation context in database with retry logic"""
    for attempt in range(3):  # Try up to 3 times
        try:
            db = get_db_with_retry()
            # Convert session_id to UUID format if needed
            from uuid import UUID
            try:
                uuid_session_id = UUID(session_id)
            except ValueError:
                # If it's not a valid UUID, return (can't store in DB)
                logger.warning(f"Invalid session ID format for DB storage: {session_id}")
                return

            # Create new message
            db_message = ChatMessage(
                session_id=uuid_session_id,
                role=role,
                content=content,
                sources=sources
            )
            db.add(db_message)
            db.commit()
            return  # Success
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} to add message to DB failed: {e}")
            if attempt == 2:  # Last attempt
                # Fallback to in-memory storage
                logger.warning("Falling back to in-memory storage for adding message")
                if session_id not in conversation_contexts:
                    conversation_contexts[session_id] = []
                conversation_contexts[session_id].append({
                    "role": role,
                    "content": content,
                    "timestamp": datetime.now().isoformat()
                })
            time.sleep(0.1 * (2 ** attempt))  # Exponential backoff
        finally:
            try:
                db.close()
            except:
                pass




def add_message_to_context(session_id: str, role: str, content: str, sources: List[Dict[str, Any]] = None):
    """Add a message to the conversation context with database storage and fallback"""
    # Add to database with retry logic
    add_message_to_context_in_db(session_id, role, content, sources)

    # Also add to in-memory for immediate access
    if session_id not in conversation_contexts:
        conversation_contexts[session_id] = []
    conversation_contexts[session_id].append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    })

def run_agent_with_context(query: str, session_id: str = "default", max_tokens: int = 1000, temperature: float = 0.3):
    """Run the AI agent with RAG context and conversation history"""
    # Acquire session lock to prevent concurrent requests for the same session
    if session_id not in session_locks:
        session_locks[session_id] = threading.Lock()

    with session_locks[session_id]:
        try:
                # Retrieve relevant context
            retrieved_texts = retrieve(query, limit=5)

            # Format the context from retrieved chunks
            context_text = "\n\n".join(retrieved_texts)

            # Get conversation history for context
            conversation_history = get_conversation_context(session_id)

            # Create the system message with context
            system_message = f"""You are an AI tutor for the Physical AI & Humanoid Robotics textbook.
Use the following context to answer the user's question.
If the context doesn't contain relevant information, say so.
Be accurate, concise, and cite sources when possible.

Context: {context_text}"""

            # Prepare messages with conversation history
            messages = [
                {"role": "system", "content": system_message}
            ]

            # Add conversation history (limit to last 10 messages to prevent token overflow)
            recent_history = conversation_history[-10:] if len(conversation_history) > 10 else conversation_history
            for msg in recent_history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

            # Add the current query
            messages.append({"role": "user", "content": query})

            # Make the API call with network error handling
            response = None
            for attempt in range(3):  # Retry up to 3 times for network issues
                try:
                    response = client.chat.completions.create(
                        model="mistralai/devstral-2512:free",
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    break  # Success, exit the retry loop
                except Exception as api_error:
                    logger.warning(f"API call attempt {attempt + 1} failed: {api_error}")
                    if attempt == 2:  # Last attempt
                        raise api_error
                    time.sleep(1 * (2 ** attempt))  # Exponential backoff

            # Create source attribution data
            sources = []
            for text in retrieved_texts:
                sources.append({
                    "content": text,
                    "title": "Retrieved Content",
                    "file_path": "unknown",
                    "score": 1.0  # Placeholder score
                })

            # Add the user query and AI response to conversation context with sources
            add_message_to_context(session_id, "user", query, sources)
            ai_response = response.choices[0].message.content
            add_message_to_context(session_id, "assistant", ai_response, sources)

            return ai_response

        except ConnectionError as e:
            logger.error(f"Network connection error in agent: {e}")
            raise Exception(f"Network connection error: {str(e)}")
        except TimeoutError as e:
            logger.error(f"Request timeout in agent: {e}")
            raise Exception(f"Request timeout: {str(e)}")
        except Exception as e:
            logger.error(f"Error running agent: {e}")
            # Check for specific network-related errors
            error_str = str(e).lower()
            if any(keyword in error_str for keyword in ["connection", "timeout", "network", "ssl", "ssl handshake"]):
                raise Exception(f"Network error: {str(e)}")
            raise Exception(f"Agent error: {str(e)}")

def clear_conversation_context(session_id: str):
    """Clear conversation history for a session"""
    if session_id in conversation_contexts:
        conversation_contexts[session_id] = []

def get_conversation_summary(session_id: str) -> Dict[str, Any]:
    """Get a summary of the conversation"""
    context = get_conversation_context(session_id)
    return {
        "session_id": session_id,
        "message_count": len(context),
        "last_updated": context[-1]["timestamp"] if context else None,
        "messages": context
    }