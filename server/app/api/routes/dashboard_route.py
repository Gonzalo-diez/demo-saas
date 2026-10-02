from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.core.rate_limit import limiter
from app.db.base import get_db
from app.core.dependencies import get_current_active_user
from app.models.sales_rep_model import SalesRep
from app.schemas.dashboard_schema import DashboardSummaryResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/summary", response_model=DashboardSummaryResponse)
@limiter.limit("50/minute")
def get_dashboard_summary(
    request: Request,
    db: Session = Depends(get_db),
    _: SalesRep = Depends(get_current_active_user),
):
    service = DashboardService(db)
    return service.get_summary()