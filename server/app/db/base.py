from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.SQL_ECHO,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_with_commit(db: Session = Depends(get_db)):
    # Depende de get_db a propósito: FastAPI cachea las dependencias por
    # request, así get_db y get_db_with_commit comparten LA MISMA sesión.
    # Si fueran dos sesiones, el tenant que atan las dependencias de auth
    # (sobre get_db) no valdría para la sesión que usa el endpoint.
    try:
        yield db
        db.commit()

    except Exception:
        db.rollback()
        raise

# Registra los eventos de aislamiento por tenant sobre Session (filtro
# automático por tenant_id + sellado en los INSERT). Debe quedar al final,
# una vez definido Base. Ver app/db/tenant_context.py.
import app.db.tenant_context  # noqa: E402,F401
