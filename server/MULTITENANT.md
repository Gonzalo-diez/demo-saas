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

## Roles y quién crea qué

| Rol | Dónde vive | Login | Qué puede |
|---|---|---|---|
| **Admin de plataforma** | tabla `admins` (sin tenant) | `POST /api/admin/login` (cookie `PLATFORM_AUTH_COOKIE_NAME`) | Crear / listar / activar / desactivar distribuidoras (`/api/tenants/*`) y crear otros admins (`/api/admin/users`) |
| **Superusuario de distribuidora** | `sales_reps` con `is_superuser` | `POST /api/sales-reps/login` + `X-Tenant-Slug` | Crear vendedores y administrar todo lo de **su** tenant |
| **Vendedor** | `sales_reps` | idem | Operar dentro de su tenant (no crea vendedores) |
| **Cliente B2B** | `clients` | `POST /api/clients/login` + `X-Tenant-Slug` | Catálogo y pedidos de su tenant |

Los tokens no se cruzan: el del admin de plataforma (`type=platform_admin`, sin `tenant_id`) no
sirve en ninguna ruta de distribuidora, y el de un vendedor/cliente no sirve en `/api/tenants/*`
ni en `/api/admin/*`.

El primer admin de plataforma se crea al arrancar con `FIRST_ADMIN_EMAIL` / `FIRST_ADMIN_PASSWORD`.

```bash
# 1) Login del admin de plataforma (guarda la cookie)
curl -c adm.jar -X POST http://localhost:8000/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"..."}'

# 2) Crear una distribuidora con su primer administrador
curl -b adm.jar -X POST http://localhost:8000/api/tenants/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Distri Oeste","slug":"distri-oeste",
       "domain":"https://tienda.distri-oeste.com",
       "admin_email":"admin@oeste.com","admin_password":"secreto123"}'

# 3) Ese admin entra a su distribuidora y crea vendedores
curl -c t.jar -X POST http://localhost:8000/api/sales-reps/login \
  -H "X-Tenant-Slug: distri-oeste" -H "Content-Type: application/json" \
  -d '{"email":"admin@oeste.com","password":"secreto123"}'
curl -b t.jar -X POST http://localhost:8000/api/sales-reps/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Vendedor Uno","email":"v1@oeste.com","password":"vend1234"}'
```

Endpoints de plataforma: `POST /api/admin/login|logout`, `GET /api/admin/me`,
`GET|POST /api/admin/users`, `PATCH|DELETE /api/admin/users/{id}` (no podés desactivarte ni
borrarte a vos mismo) y `GET|POST|PATCH /api/tenants/`, `PATCH /api/tenants/{id}/activate|deactivate`.

Públicos: `GET /api/tenants/slug/{slug}` y `GET /api/tenants/by-domain/{domain}`
(id/name/slug/domain/logo) y, autenticado, `GET /api/tenants/me`.

## Tienda pública de cada distribuidora (dominio + compra con registro)

- **Dominio obligatorio al crear un tenant** (`domain`): se acepta un dominio o una URL
  (`https://Tienda.X.com:8443/inicio`) y se guarda solo el host (`tienda.x.com`, minúsculas,
  sin esquema/puerto/path). Es único entre distribuidoras y editable con `PATCH /api/tenants/{id}`.
  `tienda.x.com` y `www.tienda.x.com` llegan a la misma distribuidora. IPs no se aceptan.
- **Cómo se identifica la tienda**: el frontend manda el host con el que entró el visitante en
  el header `X-Tenant-Domain` (o consulta `GET /api/tenants/by-domain/{host}` para armar la
  página). Prioridad cuando no hay token: `X-Tenant-Slug` > `X-Tenant-Domain` > `X-Tenant-ID`.
  Con un token válido manda siempre el tenant del token y los headers se ignoran.
- **Catálogo sin login**: `GET /api/products/`, `/api/products/{id}`, `/api/products/filters`,
  `/api/categories/` y `/api/categories/{id}` los puede llamar un visitante. Ve solo lo publicado
  (producto público + activo + categoría pública) y sin datos internos: la respuesta de tienda
  (`PublicProductResponse`) no trae `unit_cost`, `stock_min` ni estado. El personal (vendedores)
  sigue viendo todo, con costo.
- **Registro recién al comprar**: mirar y armar el carrito no pide cuenta. Al finalizar,
  el frontend llama `POST /api/clients/register` (name, email, password, phone; opcional
  tax_id / client_type). Crea el cliente en esa distribuidora, deja la sesión iniciada
  (cookie) y devuelve el cliente; después `POST /api/orders` ya funciona. Si el email ya existe
  en esa distribuidora responde 409 (el frontend ofrece "iniciar sesión": `POST /api/clients/login`).
  `POST /api/orders` sin sesión sigue respondiendo 401.
- **CORS**: además de `CORS_ORIGINS`, se aceptan los orígenes cuyo host sea el dominio de una
  distribuidora **activa** (caché de 60 s, se invalida al crear/editar/activar/desactivar tenants).
- **Cookies**: son por host. Lo más simple es que cada tienda llame a `/api/*` en su mismo
  dominio (rewrite/proxy del frontend hacia el backend) y mande `X-Tenant-Domain`. Si el frontend
  y la API quedan en dominios distintos hay que usar `AUTH_COOKIE_SAMESITE=none` + `AUTH_COOKIE_SECURE=true`.
- Dev: `*.localhost` resuelve a 127.0.0.1 en los navegadores (`distri-norte.localhost:3000`).
  El tenant inicial usa `FIRST_TENANT_DOMAIN` (default `main.localhost`).
- La migración `d4a8e1b7c3f9` pone `<slug>.localhost` a las distribuidoras que ya existían:
  hay que cambiarlo por el dominio real.

## Categorías y publicación (cada distribuidora arma lo suyo)

Ya no hay una lista fija de categorías en el código: cada distribuidora crea las suyas
(`/api/categories`) y decide qué ve el cliente en el catálogo.

| Qué | Cómo |
|---|---|
| Crear / editar / borrar categoría | `POST/PATCH/DELETE /api/categories/` (solo se borra si no tiene productos) |
| Publicar / ocultar categoría | `PATCH /api/categories/{id}/publish` · `/unpublish` (o `is_public` en el body) |
| Publicar / ocultar producto | `PATCH /api/products/{id}/publish` · `/unpublish` (o `is_public` al crear/editar) |
| Elegir categoría de un producto | `category_id` al crear/editar el producto |
| Pedir DNI + mayoría de edad en pedidos online | `requires_age_verification` en la categoría (antes estaba fijo para 3 categorías de tabaco) |

**Qué ve un cliente**: productos *activos* + *publicados* cuya categoría (si tiene) también
es *pública*. Un cliente no puede saltearlo con filtros (`is_active`, `is_public`,
`catalog_only`), pide un producto oculto y recibe 404, y no puede pedirlo en la tienda.
El personal ve todo; `GET /api/products/?catalog_only=true` previsualiza lo que ven los clientes.

**Importaciones / `category` como texto**: se busca la categoría por nombre (sin importar
mayúsculas ni tildes) y, si no existe, se crea **privada**: nada se publica solo.
Después se publica desde Categorías. Una imagen solo es obligatoria si el producto se va a ver
en el catálogo (producto público + categoría pública).

**Migración de datos** (`7c1d9e4a52b8`): crea una categoría por cada nombre ya usado en cada
distribuidora. Las que estaban en la lista fija quedan públicas (y las de tabaco con
verificación de edad); las "libres" quedan privadas, igual que se comportaban antes.
`products.category` sigue guardando una copia del nombre (la mantiene sincronizada al renombrar).

El endpoint viejo `GET /api/products/categories` se reemplazó por `GET /api/categories/`.

**Imagen de categoría** (`image_url`, igual que en producto): una categoría **pública** necesita
imagen (400 si falta, o si se la quiere publicar/quitar la imagen estando pública); una privada
puede no tenerla. Subida: `POST /api/upload/category-image` (superusuario) devuelve la URL para
`image_url`. La tienda recibe `image_url` en `GET /api/categories/`.

## Puesta en marcha de la demo

```bash
cp .env.example .env            # completar JWT_SECRET, FIRST_ADMIN_EMAIL/PASSWORD, etc.
alembic upgrade head            # base nueva
python -m app.scripts.seed_demo # 2 distribuidoras de ejemplo (clave demo1234)
uvicorn app.main:app --reload
```

Probar: `POST /api/sales-reps/login` con `X-Tenant-Slug: distri-norte` y
`admin@distri-norte.com` / `demo1234`; repetir con `distri-sur` y comparar `GET /api/products/`.

## Qué tiene que hacer el frontend

- Login (staff y cliente): mandar `X-Tenant-Slug` (o `tenant_slug` en el body). En la tienda
  pública, mandar `X-Tenant-Domain` con el host actual (`window.location.host`).
- Tracking público de analytics (`POST /api/analytics/events[/bulk]`): mandar `X-Tenant-Slug`
  o `X-Tenant-Domain` si el visitante no tiene sesión.
- Alta de distribuidora (panel de plataforma): campo **dominio / URL de la tienda** obligatorio.
- Form de categoría: campo imagen (subir con `/api/upload/category-image`); obligatorio si es pública.
- Tienda: catálogo y categorías sin login; pedir registro/login recién al finalizar la compra
  (`POST /api/clients/register`), y recién ahí `POST /api/orders`.
- Se eliminaron `GET /api/clients/map`, `GET /api/sales-reps/map` y todo `/api/ai/*` (Gemini):
  sacar esas pantallas del frontend.
- Las cookies/token existentes quedan inválidas: hay que volver a iniciar sesión.
- Pantalla de categorías (alta, público/privado, borrar) y un switch "publicado" en cada
  producto; el alta de producto elige `category_id` desde `GET /api/categories/` (ya no
  existe `GET /api/products/categories`).

## Límites a tener en cuenta

- Las sentencias `text()`/Core sobre `Model.__table__` no pasan por el filtro
  automático (hoy no hay ninguna). Si se agregan, filtrar con `require_tenant_id(db)`.
- WhatsApp: un solo número de la plataforma; el tenant se resuelve por el pedido
  (id del botón). Para un número por distribuidora habría que guardarlo en `Tenant`.
- Para endurecer más: Postgres Row-Level Security como segunda barrera.
- Los `.env` originales traían claves reales (Gemini, Cloudinary, WhatsApp, Resend):
  conviene rotarlas (la de Gemini ya no se usa: revocarla).

## Historial de compras, vencimiento y precio por % de remarque

- **Precio de venta por remarque**: al crear un producto (`POST /api/products/`) se manda
  `unit_price` **o** `markup_percent`. Con remarque, el precio se calcula sobre el costo y se
  **redondea al peso entero** (mitad hacia arriba): costo 200 + 40% = 280 · 400,50 → 401 · 400,49 → 400.
  Si vienen los dos, manda el remarque. El % queda guardado en `products.markup_percent`;
  `PATCH /api/products/{id}` con `markup_percent` (sin `unit_price`) recalcula el precio, y un
  `unit_price` puesto a mano borra el remarque guardado. Cálculo en `app/utils/pricing.py`.
- **Historial de compras** (`product_purchases`): cada ingreso de mercadería queda registrado
  con fecha, cantidad, costo, % de remarque, precio de venta fijado, vencimiento y origen
  (`initial_stock`, `manual`, `purchase_invoice`, `import`). Es un registro: no se edita ni se borra.
  - `GET /api/products/{id}/purchases/` → lista (la más reciente primero, paginada) + `summary`
    (costo promedio ponderado, último / mínimo / máximo costo, próximo vencimiento).
  - `POST /api/products/{id}/purchases/` → registra una compra: suma stock (movimiento `purchase`),
    recalcula el costo promedio ponderado y, si trae `markup_percent` o `sale_price`, actualiza el precio
    de venta del producto (`update_product_price=false` lo deja como está).
  - Se alimenta solo desde: el stock inicial al crear un producto (con `expiry_date` opcional), los
    remitos de compra confirmados y las importaciones Excel. La migración `e5b9f2c8d4a1` crea una
    entrada inicial para los productos que ya tenían stock.
  - `products.unit_cost` sigue siendo el costo **promedio ponderado**; el costo de cada compra
    está en el historial.
  - El "próximo vencimiento" es una referencia: no descuenta lo ya vendido de cada compra.
- Corregido: la importación Excel de un producto **nuevo** con stock lo dejaba con el doble.

## Cookies y rate limit detrás del frontend (proxy de `/api`)

- **Sesión:** la cookie la pone el backend con `SameSite=Lax` y es del host que la recibe. Si el
  navegador llama a la API en OTRO sitio (ej. tienda en `distri-norte.localhost:3000` y API en
  `localhost:8000`) la descarta y `/api/sales-reps/me` da 401 aunque el login dé 200. El frontend
  evita esto llamando a `/api` en el mismo dominio de la tienda (Next lo reenvía al backend): no hace
  falta tocar el backend. Solo si la API queda en otro sitio en producción: `AUTH_COOKIE_SAMESITE=none` +
  `AUTH_COOKIE_SECURE=true`.
- **Rate limit:** detrás de un proxy, el backend ve la IP del proxy para todos y comparten un mismo cupo
  (ej. 5 logins por minuto en TODA la plataforma). Con `TRUSTED_PROXY_HOPS=N` (cuántos proxies tuyos hay
  delante; normalmente 1) se usa la IP real de `X-Forwarded-For`: la N-ésima desde la derecha, la que
  agregó tu proxy. Ponelo SOLO si delante hay un proxy tuyo que agrega esa IP (nginx, Cloudflare, el
  balanceador): si el backend o Next quedan expuestos directo, el cliente podría inventar su IP y esquivar
  el límite. Sin proxy de borde (ej. demo local con `next dev`) la IP real no llega: dejá
  `TRUSTED_PROXY_HOPS=0` y, si hay varios usuarios probando, `RATE_LIMIT_ENABLED=False`.
  (Si el backend corre con `--proxy-headers` y `--forwarded-allow-ips`, uvicorn ya reescribe la IP; no hace
  falta duplicarlo con `TRUSTED_PROXY_HOPS`.)
