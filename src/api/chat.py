from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any, List
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from src.services.retrieving import retrieve
from src.services.llm_service import llm_service
from src.services.agent import run_agent_with_context
from src.models.chat_conversation import ChatConversation, ChatConversationCreate, ChatConversationUpdate, Message
from src.services.chat_conversation_service import ChatConversationService
import logging
import time
from collections import defaultdict
import html
import re

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Simple in-memory rate limiter
request_counts = defaultdict(list)  # Maps IP -> list of request timestamps
RATE_LIMIT = 10  # Max 10 requests
RATE_LIMIT_WINDOW = 60  # Per 60 seconds

def is_rate_limited(request: Request) -> bool:
    """Check if the request exceeds rate limits"""
    client_ip = request.client.host if request.client else "unknown"

    now = time.time()
    # Remove requests older than the time window
    request_counts[client_ip] = [req_time for req_time in request_counts[client_ip]
                                 if now - req_time < RATE_LIMIT_WINDOW]

    # Check if we've exceeded the limit
    if len(request_counts[client_ip]) >= RATE_LIMIT:
        return True

    # Add current request to the list
    request_counts[client_ip].append(now)
    return False

def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent injection attacks"""
    if not text:
        return text

    # Remove potentially dangerous characters/sequences
    sanitized = html.escape(text)

    # Remove control characters except basic whitespace
    sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', sanitized)

    # Limit length to prevent overly large inputs
    if len(sanitized) > 5000:  # 5000 characters max
        sanitized = sanitized[:5000]

    return sanitized

router = APIRouter()

class ChatMessageRequest(BaseModel):
    content: str
    context_window: int = 5  # Number of context chunks to retrieve

class ChatSessionRequest(BaseModel):
    title: str = "New Chat Session"

@router.post("/sessions")
async def create_chat_session(request: ChatSessionRequest = None):
    """Create a new chat session"""
    if request is None:
        request = ChatSessionRequest()

    # In a real implementation, you would create a session in the database
    # For now, we'll return a sample session
    session_id = "session_" + str(hash(request.title))[:8]
    return {"session_id": session_id, "title": request.title, "created_at": "2025-12-11T00:00:00Z"}

@router.post("/sessions/{session_id}/messages")
async def send_chat_message(request: Request, session_id: str, chat_request: ChatMessageRequest):
    """Send a message in a chat session and get RAG-enhanced response with conversation context and source attribution"""
    # Check rate limit
    if is_rate_limited(request):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later."
        )

    try:
        # Sanitize input
        sanitized_content = sanitize_input(chat_request.content)
        sanitized_context_window = max(1, min(chat_request.context_window, 10))  # Limit context window between 1-10

        # Retrieve relevant context
        retrieved_texts = retrieve(sanitized_content, limit=sanitized_context_window)

        # Format the context from retrieved chunks
        context_text = "\n\n".join([text["content"] if isinstance(text, dict) else str(text) for text in retrieved_texts])

        # Create the system message with context
        system_message = f"""You are an AI assistant for the Physical AI & Humanoid Robotics textbook.
Use the following context to answer the user's question.
If the context doesn't contain relevant information, say so.
Be accurate, concise, and cite sources when possible.

Context: {context_text}"""

        # Prepare messages with conversation history
        from src.services.agent import get_conversation_context
        conversation_history = get_conversation_context(session_id)

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
        messages.append({"role": "user", "content": sanitized_content})

        # Create source attribution data
        sources = []
        for text in retrieved_texts:
            if isinstance(text, dict):
                sources.append({
                    "content": text.get("content", ""),
                    "title": text.get("title", "Retrieved Content"),
                    "file_path": text.get("file_path", "unknown"),
                    "score": text.get("score", 1.0),
                    "metadata": text.get("metadata", {})
                })
            else:
                # Handle both string and dict formats from retrieve function
                if hasattr(text, '__getitem__'):  # dict-like
                    sources.append({
                        "content": text.get("content", "") if isinstance(text, dict) else str(text),
                        "title": text.get("title", "Retrieved Content") if isinstance(text, dict) else "Retrieved Content",
                        "file_path": text.get("file_path", "unknown") if isinstance(text, dict) else "unknown",
                        "score": text.get("score", 1.0) if isinstance(text, dict) else 1.0,
                        "metadata": text.get("metadata", {}) if isinstance(text, dict) else {}
                    })
                else:
                    sources.append({
                        "content": str(text),
                        "title": "Retrieved Content",
                        "file_path": "unknown",
                        "score": 1.0,
                        "metadata": {}
                    })

        # Use the LLM service with source attribution
        result = llm_service.chat_completion_with_sources(
            messages=messages,
            sources=sources,
            temperature=0.3,
            max_tokens=1000
        )

        # Add the user query and AI response to conversation context
        from src.services.agent import add_message_to_context
        add_message_to_context(session_id, "user", sanitized_content, sources)
        add_message_to_context(session_id, "assistant", result["response"], sources)

        return {
            "session_id": session_id,
            "response": result["response"],
            "sources": result["sources"],
            "query": sanitized_content,
            "retrieved_chunks": len(retrieved_texts),
            "usage": result.get("usage", {})
        }

    except ValueError as e:
        # Handle configuration/value errors (like missing API keys)
        logger.error(f"Configuration error processing chat message: {e}")
        raise HTTPException(status_code=400, detail=f"Configuration error: {str(e)}")
    except SQLAlchemyError as e:
        # Handle database errors specifically
        logger.error(f"Database error processing chat message: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        error_msg = str(e)
        if "API key" in error_msg or "auth" in error_msg.lower():
            logger.warning("Authentication error - API key missing or invalid")
            # Return a graceful response instead of throwing an exception
            return {
                "session_id": session_id,
                "response": "I'm sorry, but I'm currently unable to connect to the AI service. Please check that your API keys are configured correctly.",
                "sources": [],
                "query": sanitized_content,
                "retrieved_chunks": 0,
                "usage": {}
            }
        elif "rate limit" in error_msg.lower() or "quota" in error_msg.lower():
            logger.warning("Rate limit exceeded")
            return {
                "session_id": session_id,
                "response": "I'm sorry, but I've reached the rate limit for the AI service. Please try again later.",
                "sources": [],
                "query": sanitized_content,
                "retrieved_chunks": 0,
                "usage": {}
            }
        elif "timeout" in error_msg.lower():
            logger.warning("Request timeout")
            return {
                "session_id": session_id,
                "response": "I'm sorry, but the request timed out. Please try again.",
                "sources": [],
                "query": sanitized_content,
                "retrieved_chunks": 0,
                "usage": {}
            }
        elif "database" in error_msg.lower() or "connection" in error_msg.lower():
            logger.error("Database connection error")
            return {
                "session_id": session_id,
                "response": "I'm sorry, but there's a connection issue with the database. Please try again later.",
                "sources": [],
                "query": sanitized_content,
                "retrieved_chunks": 0,
                "usage": {}
            }
        else:
            logger.error(f"General error: {error_msg}")
            return {
                "session_id": session_id,
                "response": "I'm sorry, there was an error processing your request. Please try again.",
                "sources": [],
                "query": sanitized_content,
                "retrieved_chunks": 0,
                "usage": {}
            }

@router.post("/ask-from-selection")
async def ask_from_selection(request: Request, chat_request: ChatMessageRequest):
    """Ask a question about selected/highlighted text with conversation context and source attribution"""
    # Check rate limit
    if is_rate_limited(request):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later."
        )

    try:
        # Sanitize input
        sanitized_content = sanitize_input(chat_request.content)
        sanitized_context_window = max(1, min(chat_request.context_window, 10))  # Limit context window between 1-10

        # First retrieve the context to get sources
        retrieved_texts = retrieve(sanitized_content, limit=sanitized_context_window)

        # Format sources properly
        sources = []
        for text in retrieved_texts:
            if isinstance(text, dict):
                sources.append({
                    "content": text.get("content", ""),
                    "title": text.get("title", "Retrieved Content"),
                    "file_path": text.get("file_path", "unknown"),
                    "score": text.get("score", 1.0),
                    "metadata": text.get("metadata", {})
                })
            else:
                # Handle both string and dict formats from retrieve function
                if hasattr(text, '__getitem__'):  # dict-like
                    sources.append({
                        "content": text.get("content", "") if isinstance(text, dict) else str(text),
                        "title": text.get("title", "Retrieved Content") if isinstance(text, dict) else "Retrieved Content",
                        "file_path": text.get("file_path", "unknown") if isinstance(text, dict) else "unknown",
                        "score": text.get("score", 1.0) if isinstance(text, dict) else 1.0,
                        "metadata": text.get("metadata", {}) if isinstance(text, dict) else {}
                    })
                else:
                    sources.append({
                        "content": str(text),
                        "title": "Retrieved Content",
                        "file_path": "unknown",
                        "score": 1.0,
                        "metadata": {}
                    })

        # Use the LLM service with RAG context for selection-based queries
        from src.services.llm_service import llm_service

        # Format the context from retrieved chunks
        context_text = "\n\n".join([text["content"] if isinstance(text, dict) else str(text) for text in retrieved_texts])

        # Create the system message with context
        system_message = f"""You are an AI assistant for the Physical AI & Humanoid Robotics textbook.
Use the following context to answer the user's question about the selected text.
If the context doesn't contain relevant information, say so.
Be accurate, concise, and cite sources when possible.

Context: {context_text}"""

        # Prepare messages for the LLM (no conversation history for selection-based queries)
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": sanitized_content}
        ]

        # Use the LLM service with source attribution
        result = llm_service.chat_completion_with_sources(
            messages=messages,
            sources=sources,
            temperature=0.3,
            max_tokens=1000
        )

        return {
            "response": result["response"],
            "sources": result["sources"],
            "selected_text": sanitized_content,
            "retrieved_chunks": len(retrieved_texts),
            "usage": result.get("usage", {})
        }

    except ValueError as e:
        # Handle configuration/value errors (like missing API keys)
        logger.error(f"Configuration error processing selection-based question: {e}")
        raise HTTPException(status_code=400, detail=f"Configuration error: {str(e)}")
    except SQLAlchemyError as e:
        # Handle database errors specifically
        logger.error(f"Database error processing selection-based question: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        # Handle connection errors (like Qdrant/LLM provider connection issues) and other errors
        logger.error(f"Error processing selection-based question: {e}")
        error_msg = str(e)
        if "API key" in error_msg or "auth" in error_msg.lower():
            logger.warning("Authentication error - API key missing or invalid")
            return {
                "response": "I'm sorry, but I'm currently unable to connect to the AI service. Please check that your API keys are configured correctly.",
                "sources": [],
                "selected_text": sanitized_content,
                "retrieved_chunks": 0,
                "usage": {}
            }
        elif "rate limit" in error_msg.lower() or "quota" in error_msg.lower():
            logger.warning("Rate limit exceeded")
            return {
                "response": "I'm sorry, but I've reached the rate limit for the AI service. Please try again later.",
                "sources": [],
                "selected_text": sanitized_content,
                "retrieved_chunks": 0,
                "usage": {}
            }
        elif "timeout" in error_msg.lower():
            logger.warning("Request timeout")
            return {
                "response": "I'm sorry, but the request timed out. Please try again.",
                "sources": [],
                "selected_text": sanitized_content,
                "retrieved_chunks": 0,
                "usage": {}
            }
        elif "database" in error_msg.lower() or "connection" in error_msg.lower():
            logger.error("Database connection error")
            return {
                "response": "I'm sorry, but there's a connection issue with the database. Please try again later.",
                "sources": [],
                "selected_text": sanitized_content,
                "retrieved_chunks": 0,
                "usage": {}
            }
        else:
            logger.error(f"General error: {error_msg}")
            return {
                "response": "I'm sorry, there was an error processing your request. Please try again.",
                "sources": [],
                "selected_text": sanitized_content,
                "retrieved_chunks": 0,
                "usage": {}
            }


@router.get("/sessions")
async def get_chat_sessions():
    """Get user's chat sessions (placeholder implementation)"""
    # In a real implementation, this would query the database for user's sessions
    # For now, return an empty list as a placeholder
    return {
        "sessions": []
    }


@router.get("/sessions/{session_id}/messages")
async def get_chat_session_messages(session_id: str):
    """Get messages from a specific chat session (placeholder implementation)"""
    # In a real implementation, this would query the database for session messages
    # For now, return an empty list as a placeholder
    from src.services.agent import get_conversation_summary
    summary = get_conversation_summary(session_id)
    return {
        "messages": summary["messages"],
        "session_id": session_id,
        "message_count": summary["message_count"]
    }


# Initialize chat service for conversation persistence
chat_service = ChatConversationService()


@router.post("/conversation")
async def create_or_update_conversation(conversation_data: ChatConversationCreate):
    """
    Create a new conversation or continue an existing one
    This endpoint supports client-side persistence by creating or updating conversations
    """
    try:
        # If conversation_id is provided, update existing conversation
        if conversation_data.messages and len(conversation_data.messages) > 0:
            # For the purpose of this implementation, we'll create a new conversation with the provided data
            # In a real implementation, this would handle ongoing conversations
            new_conversation = await chat_service.create_conversation(conversation_data)

            # Return the conversation ID and a placeholder response
            # In a real implementation, this would call an AI service to generate a response
            latest_message = conversation_data.messages[-1] if conversation_data.messages else None
            response_message = Message(
                role="assistant",
                content=f"I received your message: '{latest_message.content if latest_message else 'Hello'}'. This is a simulated response from the backend.",
                timestamp=new_conversation.updated_at
            )

            # Add the response to the conversation
            updated_conversation = await chat_service.add_message(new_conversation.id, response_message)

            return {
                "conversationId": updated_conversation.id,
                "response": response_message.content,
                "timestamp": response_message.timestamp.isoformat()
            }
        else:
            # Create a new conversation with no initial messages
            new_conversation = await chat_service.create_conversation(
                ChatConversationCreate(user_id=conversation_data.user_id, messages=[])
            )

            return {
                "conversationId": new_conversation.id,
                "response": "New conversation started",
                "timestamp": new_conversation.created_at.isoformat()
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating/updating conversation: {str(e)}")


@router.get("/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    """
    Get conversation history
    This endpoint works with persisted conversations
    """
    try:
        conversation = await chat_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return {
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat()
                }
                for msg in conversation.messages
            ],
            "lastUpdated": conversation.updated_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving conversation: {str(e)}")


@router.post("/conversation/{conversation_id}")
async def add_message_to_conversation(conversation_id: str, message: Message):
    """
    Add a message to an existing conversation
    """
    try:
        updated_conversation = await chat_service.add_message(conversation_id, message)
        if not updated_conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return {
            "conversationId": updated_conversation.id,
            "messageAdded": True,
            "messageCount": len(updated_conversation.messages)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding message to conversation: {str(e)}")


@router.get("/user/{user_id}/conversations")
async def get_user_conversations(user_id: str):
    """
    Get all conversations for a user
    """
    try:
        conversations = await chat_service.get_user_conversations(user_id)

        return {
            "conversations": [
                {
                    "id": conv.id,
                    "messageCount": len(conv.messages),
                    "createdAt": conv.created_at.isoformat(),
                    "updatedAt": conv.updated_at.isoformat()
                }
                for conv in conversations
            ],
            "total": len(conversations)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving user conversations: {str(e)}")


@router.put("/conversation/{conversation_id}")
async def update_conversation(conversation_id: str, update_data: ChatConversationUpdate):
    """
    Update a conversation with new data
    """
    try:
        updated_conversation = await chat_service.update_conversation(conversation_id, update_data)
        if not updated_conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return updated_conversation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating conversation: {str(e)}")