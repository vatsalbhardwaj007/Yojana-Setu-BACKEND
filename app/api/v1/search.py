from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status

from app.schemas.catalog import (
    SchemeSearchResponse,
    TranscriptionConfigResponse,
    TranscriptionResponse,
)
from app.services.search_service import SemanticSearchService
from app.services.transcription_service import (
    TranscriptionError,
    TranscriptionService,
    TranscriptionUnavailableError,
)

router = APIRouter(prefix="/search", tags=["Search"])


def get_search_service() -> SemanticSearchService:
    """Dependency provider for SemanticSearchService."""
    return SemanticSearchService()


def get_transcription_service() -> TranscriptionService:
    """Dependency provider for TranscriptionService."""
    return TranscriptionService()


SearchServiceDep = Annotated[SemanticSearchService, Depends(get_search_service)]
TranscriptionServiceDep = Annotated[TranscriptionService, Depends(get_transcription_service)]


@router.get("", response_model=SchemeSearchResponse)
def search_schemes(
    q: Annotated[str, Query(min_length=1, description="Natural-language scheme search query")],
    service: SearchServiceDep,
    limit: Annotated[int, Query(ge=1, le=20, description="Max results to return")] = 10,
):
    """Semantic search over the scheme catalogue using deterministic lexical matching."""
    return service.search(query=q, limit=limit)


@router.get("/config", response_model=TranscriptionConfigResponse)
def transcription_config(service: TranscriptionServiceDep):
    """Report speech-to-text capabilities so the frontend can choose its STT path."""
    return TranscriptionConfigResponse(server_stt_configured=service.is_configured())


@router.post("/transcribe", response_model=TranscriptionResponse)
def transcribe_audio(audio: UploadFile, service: TranscriptionServiceDep):
    """Transcribe an uploaded audio recording using the Gemini API."""
    try:
        audio_bytes = audio.file.read()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not read the uploaded audio.",
        )
    if not audio_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty audio upload received.",
        )
    try:
        text = service.transcribe(
            audio_bytes,
            filename=audio.filename or "audio.webm",
            content_type=audio.content_type or "audio/webm",
        )
    except TranscriptionUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Speech transcription (Gemini) is not configured. Add GEMINI_API_KEY to the backend .env.",
        )
    except TranscriptionError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )
    return TranscriptionResponse(text=text)