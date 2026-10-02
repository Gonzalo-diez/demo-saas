from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.core.rate_limit import limiter
from app.db.base import get_db_with_commit
from app.core.dependencies import get_current_active_user
from app.models.sales_rep_model import SalesRep
from app.ai.gemini.suggestion_service import GeminiSuggestionService
from app.schemas.ai_schema import (
    AiSuggestionsRequest,
    AiSuggestionsResponse,
)

router = APIRouter(prefix="/ai", tags=["AI"])

@router.post("/suggestions", response_model=AiSuggestionsResponse)
@limiter.limit("10/minute")
def get_ai_suggestions(
    request: Request,
    payload: AiSuggestionsRequest,
    db: Session = Depends(get_db_with_commit),
    _: SalesRep = Depends(get_current_active_user),
):
    service = GeminiSuggestionService(db)
    return service.get_suggestions(payload.question)