from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.security import verify_api_key
from app.db.session import get_db

from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatStatusResponse,
)
from app.schemas.common import ErrorDetailResponse
from app.services.chat_service import get_chat_status, process_chat_message

router = APIRouter(prefix="/chat", tags=["MedAssist Conversational AI"])


@router.post(
    "/message",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send health-education question to MedAssist",
    description=(
        "Processes health-education and medical terminology queries. Returns bounded educational "
        "explanations from a configured LLM provider. "
        "Strictly non-diagnostic: Never generates clinical directives, prescriptions, or patient diagnoses."
    ),
    responses={
        401: {"model": ErrorDetailResponse, "description": "Unauthorized: missing or invalid API key"},
        422: {"model": ErrorDetailResponse, "description": "Empty, malformed, or oversized message payload"},
        502: {"model": ErrorDetailResponse, "description": "External AI provider returned an error"},
        503: {"model": ErrorDetailResponse, "description": "MedAssist AI provider is not configured"},
        504: {"model": ErrorDetailResponse, "description": "External AI provider request timed out"},
    },
)
async def chat_message(
    request: ChatRequest,
    db: Session = Depends(get_db),
    _auth: bool = Depends(verify_api_key),
) -> ChatResponse:
    """Send conversational query to MedAssist health-education assistant."""
    return await process_chat_message(request, db=db)



@router.get(
    "/status",
    response_model=ChatStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get MedAssist conversational service readiness status",
    description="Returns current configuration status of MedAssist provider and active model.",
)
async def chat_status() -> ChatStatusResponse:
    """Check whether MedAssist has valid LLM provider credentials configured."""
    return get_chat_status()
