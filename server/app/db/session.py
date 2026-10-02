# Había dos engines (este y app.db.base, este último con echo=True). Ahora hay
# uno solo, definido en app.db.base; se re-exporta acá por compatibilidad.
from app.db.base import SessionLocal, engine

__all__ = ["SessionLocal", "engine"]
