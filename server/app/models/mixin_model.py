# La definición vive en app.db.mixins (sin dependencias) para que la capa de
# sesión pueda importarla sin ciclos. Se re-exporta acá por compatibilidad.
from app.db.mixins import TenantMixin

__all__ = ["TenantMixin"]
