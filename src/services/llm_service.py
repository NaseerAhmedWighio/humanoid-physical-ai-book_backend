import os
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "gemini")  # Using gemini as default
        self.client = None
        self.model = os.getenv("OPENROUTER_MODEL", "mistralai/devstral-2512:free")
        self.translation_model = os.getenv("TRANSLATION_MODEL", "google/gemma-3-4b-it:free")

        if self.provider == "gemini":
            openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
            if not openrouter_api_key:
                raise ValueError("OPENROUTER_API_KEY environment variable is required")

            self.client = OpenAI(
                api_key=openrouter_api_key,
                base_url="https://openrouter.ai/api/v1/"
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate chat completion using configured LLM provider"""
        try:
            # Extract parameters
            temperature = kwargs.get('temperature', 0.3)
            max_tokens = kwargs.get('max_tokens', 1000)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error in chat completion: {e}")
            # Re-raise with more context about LLM issues
            raise Exception(f"LLM error: {str(e)}")


    def chat_completion_with_sources(self, messages: List[Dict[str, str]], sources: List[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """Generate chat completion with source attribution"""
        try:
            # Extract parameters
            temperature = kwargs.get('temperature', 0.3)
            max_tokens = kwargs.get('max_tokens', 1000)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            ai_response = response.choices[0].message.content

            # Process sources for attribution
            attributed_sources = []
            if sources:
                # Create a simple attribution based on the content that was used
                for source in sources:
                    attributed_sources.append({
                        "content": source.get("content", "")[:200] + "..." if len(source.get("content", "")) > 200 else source.get("content", ""),
                        "title": source.get("title", "Retrieved Content"),
                        "file_path": source.get("file_path", "unknown"),
                        "score": source.get("score", 1.0),
                        "relevance": "high"  # Default relevance
                    })

            return {
                "response": ai_response,
                "sources": attributed_sources,
                "usage": {
                    "model": self.model,
                    "provider": self.provider
                }
            }

        except Exception as e:
            logger.error(f"Error in chat completion with sources: {e}")
            # Re-raise with more context about LLM issues
            raise Exception(f"LLM error: {str(e)}")

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text using FastEmbed (local)"""
        try:
            # Import the retrieving service to use FastEmbed for embeddings
            from .retrieving import get_embedding
            return get_embedding(text)
        except Exception as e:
            logger.error(f"Error in embedding: {e}")
            # Return a zero vector as fallback (BGE-small-en-v1.5 has 384 dimensions)
            return [0.0] * 384  # FastEmbed BGE-small embedding size

    def translate_text(self, text: str, target_lang: str = "ur", source_lang: str = "en", **kwargs) -> str:
        """Translate text using the configured translation model"""
        try:
            # Extract parameters
            temperature = kwargs.get('temperature', 0.3)
            max_tokens = kwargs.get('max_tokens', 1000)

            # Create a user message that includes the translation instruction
            # Some models like Google Gemma don't support system messages, so we include the instruction in the user message
            # Be more specific about Urdu translation
            if target_lang == "ur":
                user_message = f"""Translate the following text from {source_lang} to Urdu (ur). Use proper Urdu script (Arabic script for Urdu). Only return the translated text without any additional explanation, comments, or original text. Do not include the original text in your response. No English words should appear in the output. Translate every word to Urdu.

Text to translate:
{text}"""
            else:
                user_message = f"""Translate the following text from {source_lang} to {target_lang}. Only return the translated text without any additional explanation, comments, or original text. Do not include the original text in your response.

Text to translate:
{text}"""

            response = self.client.chat.completions.create(
                model=self.translation_model,
                messages=[
                    {"role": "user", "content": user_message}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )

            # Clean up the response to ensure it's only the translated text
            translated_text = response.choices[0].message.content

            # Remove any potential prefixing or additional text that might be included
            # This can happen when the model adds explanations despite our instructions
            if target_lang == "ur":
                import re
                # Remove any text in parentheses that looks like transliterations or English explanations
                translated_text = re.sub(r'\([^)]*\)', '', translated_text).strip()
                # Remove any extra whitespace
                translated_text = ' '.join(translated_text.split())
                # Remove any remaining English words if possible (this is a simple approach)
                # For more complex scenarios, we'd need a more sophisticated approach

            return translated_text

        except Exception as e:
            logger.error(f"Error in translation: {e}")
            # If there's an error (like rate limiting), return the original text
            if "Rate limit" in str(e):
                logger.warning("Rate limit exceeded for translation API, returning original text")
                return text  # Return original text if rate limited
            # Re-raise with more context about LLM issues
            raise Exception(f"Translation error: {str(e)}")

# Global instance
llm_service = LLMService()