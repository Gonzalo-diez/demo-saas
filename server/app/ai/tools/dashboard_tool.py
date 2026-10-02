from sqlalchemy.orm import Session

from app.services.dashboard_service import DashboardService

def get_dashboard_summary_tool(db: Session) -> dict:
    service = DashboardService(db)
    return service.get_summary()