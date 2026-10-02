from sqlalchemy.orm import Session
from app.repositories.dashboard_repository import DashboardRepository

class DashboardService:
    def __init__(self, db: Session):
        self.repo = DashboardRepository(db)

    def get_summary(self) -> dict:
        return self.repo.get_summary()