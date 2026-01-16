from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

from ..services.llm_service import llm_service

router = APIRouter()
logger = logging.getLogger(__name__)

class TranslationRequest(BaseModel):
    text: str
    target_lang: str = "ur"
    source_lang: str = "en"


class TranslationResponse(BaseModel):
    original_text: str
    translated_text: str
    target_lang: str
    source_lang: str


@router.post("/translate", response_model=TranslationResponse)
async def translate_text(request: TranslationRequest):
    """
    Translate text using the configured LLM model
    """
    try:
        # Validate input
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")

        # Perform translation using the LLM service
        translated_text = llm_service.translate_text(
            text=request.text,
            target_lang=request.target_lang,
            source_lang=request.source_lang
        )

        return TranslationResponse(
            original_text=request.text,
            translated_text=translated_text,
            target_lang=request.target_lang,
            source_lang=request.source_lang
        )
    except Exception as e:
        logger.error(f"Translation error: {e}")
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")


@router.post("/translate/batch")
async def translate_batch_texts(requests: list[TranslationRequest]):
    """
    Translate multiple texts in batch
    """
    try:
        results = []
        for req in requests:
            if not req.text.strip():
                raise HTTPException(status_code=400, detail="Text cannot be empty")

            translated_text = llm_service.translate_text(
                text=req.text,
                target_lang=req.target_lang,
                source_lang=req.source_lang
            )

            results.append(TranslationResponse(
                original_text=req.text,
                translated_text=translated_text,
                target_lang=req.target_lang,
                source_lang=req.source_lang
            ))

        return results
    except Exception as e:
        logger.error(f"Batch translation error: {e}")
        raise HTTPException(status_code=500, detail=f"Batch translation failed: {str(e)}")