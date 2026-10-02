# Multi-tenant (una distribuidora = un tenant)

## Cómo funciona

1. **Login por distribuidora.** Se manda el slug en el header `X-Tenant-Slug`
   (o `tenant_slug` en el body) a `POST /api/sales-reps/login` y
   `POST /api/clients/login`. El email es único *por distribuidora*.
2. **El tenant viaja en el JWT** (claim `tenant_id`). En requests autenticados el
   servidor **solo** usa ese claim; los headers `X-Tenant-*` se ignoran. Un token
   sin `tenant_id` (emitido antes de multi-tenant) se rechaza: hay que volver a loguear.
3. **Aislamiento automático** (`app/db/tenant_context.py`): cada sesión de base
   de datos queda atada al tenant del request. Toda lectura, UPDATE y DELETE de
   un modelo con `TenantMixin` se filtra por `tenant_id`, y todo INSERT se
   estampa con el tenant activo. Los repositories no filtran a mano.
   - Fail-closed: sin tenant en la sesión las consultas devuelven vacío y los
     inserts fallan.
   - No se puede insertar en otro tenant ni mover una fila entre tenants.
   - Código de sistema usa `unscoped(db)` (explícito y visible) o `tenant_scope(db, id)`.
4. **Jobs por tenant.** Agregaciones de analytics y barrido de notificaciones
   corren una vez por distribuidora activa, cada una en su sesión.
5. **Rutas públicas**: el tenant sale de algo firmado — token de edición de pedido
   y botones de WhatsApp llevan `tenant_id`; el tracking de analytics usa el token
   si hay, o `X-Tenant-Slug`.

## Alta de distribuidoras (administración de la plataforma)

Los endpoints `/api/tenants/*` (crear, listar, activar, desactivar) exigen el header
`X-Platform-Key` = `PLATFORM_ADMIN_KEY`. Sin esa variable quedan deshabilitados.

```bash
curl -X POST http://localhost:8000/api/tenants/ \
  -H "X-Platform-Key: $PLATFORM_ADMIN_KEY" -H "Content-Type: application/json" \
  -d '{"name":"Distri Oeste","slug":"distri-oeste",
       "admin_email":"admin@oeste.com","admin_password":"secreto123"}'
```

Públicos: `GET /api/tenants/slug/{slug}` (name/slug/logo) y, autenticado, `GET /api/tenants/me`.

## Puesta en marcha de la demo

```bash
cp .env.example .env            # completar JWT_SECRET, PLATFORM_ADMIN_KEY, etc.
alembic upgrade head            # base nueva
python -m app.scripts.seed_demo # 2 distribuidoras de ejemplo (clave demo1234)
uvicorn app.main:app --reload
```

Probar: `POST /api/sales-reps/login` con `X-Tenant-Slug: distri-norte` y
`admin@distri-norte.com` / `demo1234`; repetir con `distri-sur` y comparar `GET /api/products/`.

## Qué tiene que hacer el frontend

- Login (staff y cliente): mandar `X-Tenant-Slug` (o `tenant_slug` en el body).
- Tracking público de analytics (`POST /api/analytics/events[/bulk]`): mandar `X-Tenant-Slug`
  si el visitante no tiene sesión.
- Las cookies/token existentes quedan inválidas: hay que volver a iniciar sesión.

## Límites a tener en cuenta

- Las sentencias `text()`/Core sobre `Model.__table__` no pasan por el filtro
  automático (hoy no hay ninguna). Si se agregan, filtrar con `require_tenant_id(db)`.
- WhatsApp: un solo número de la plataforma; el tenant se resuelve por el pedido
  (id del botón). Para un número por distribuidora habría que guardarlo en `Tenant`.
- Para endurecer más: Postgres Row-Level Security como segunda barrera.
- Los `.env` originales traían claves reales (Gemini, Cloudinary, WhatsApp, Resend):
  conviene rotarlas.
