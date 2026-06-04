import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.core.config import settings
from backend.pipeline.prompt_model import prompt_model

logger = logging.getLogger(__name__)

router = APIRouter()


class AnalyzeRequest(BaseModel):
    message: str
    pdf_text: str = ""


def _call_model(model: str, content: str) -> str:
    """Call the AI model and raise RuntimeError if the model returns an error string."""
    reply = prompt_model(model, content)
    if reply.startswith("[Gemini Error]") or reply.startswith("[Ollama Error]"):
        raise RuntimeError(reply)
    return reply


@router.post("")
def analyze(req: AnalyzeRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    content = req.message
    if req.pdf_text.strip():
        content += f"\n\nResume Content:\n{req.pdf_text}"

    # Try primary model first
    try:
        return {"reply": _call_model(settings.CHAT_MODEL, content)}
    except RuntimeError as primary_err:
        logger.warning("Primary model %s failed: %s", settings.CHAT_MODEL, primary_err)

    # Fall back to secondary model
    if settings.CHAT_MODEL_FALLBACK:
        try:
            logger.info("Retrying with fallback model %s", settings.CHAT_MODEL_FALLBACK)
            return {"reply": _call_model(settings.CHAT_MODEL_FALLBACK, content)}
        except RuntimeError as fallback_err:
            logger.error(
                "Fallback model %s also failed: %s",
                settings.CHAT_MODEL_FALLBACK,
                fallback_err,
            )

    raise HTTPException(
        status_code=503,
        detail=(
            f"AI service unavailable: both {settings.CHAT_MODEL} and "
            f"{settings.CHAT_MODEL_FALLBACK} failed."
        ),
    )
