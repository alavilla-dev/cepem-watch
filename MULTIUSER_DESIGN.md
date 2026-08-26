# CEPEM Watch — Servidor central / multiusuario (diseño)

## Objetivo
Un servidor central de CEPEM que recibe los datos de time-tracking de varios
equipos/empleados, con **autenticación** y **aislamiento de datos por usuario**, más
dashboards por usuario (y una vista de administración agregada más adelante).

## Estado actual (base)
- aw-server (Python): **sin autenticación**; todos los endpoints `/api/0/*` abiertos.
- Buckets = espacio de nombres **plano y global** (`bucket_id` string). Sin usuario/owner.
- El cliente (`aw-client`) ya sabe enviar `Authorization: Bearer <token>` y reintentar
  offline (fail/persist queue). La web UI ya soporta token (`aw-api-token`).

## Arquitectura propuesta

### 1. Ingesta de datos — "envío directo" (recomendado)
Cada equipo ejecuta los watchers (ventana/AFK/screenshots) con `aw-client` apuntando al
**servidor central** (host/puerto de CEPEM), sobre TLS. Sin servidor local en cada equipo.
- Aprovecha la cola offline de `aw-client` (resiliencia ante cortes).
- Sin dependencia de `aw-sync` (Rust, que omitimos).
- CEPEM tiene WireGuard: el central puede exponerse solo por VPN/LAN.
- Alternativa (descartada de inicio): servidor local + sync periódico (más piezas).

### 2. Autenticación — token por usuario provisto por admin (recomendado)
- Un hook `@app.before_request` (junto a `extension_cors.register`, `server.py`) parsea
  `Authorization: Bearer <token>`, lo resuelve a un **usuario** y lo guarda en `flask.g`.
- Tokens y usuarios en un almacén central (tabla `users`/`tokens` o `users.toml` en el
  config dir). Rol `admin` para vistas agregadas.
- Sin token válido → `401` (salvo modo testing). La web UI ya envía el token → cambio mínimo.

### 3. Aislamiento de datos — prefijo en `bucket_id` (elegido)
- Una sola BD. Cada usuario tiene un prefijo (`<user>/`) aplicado a sus `bucket_id`.
- **Transparente para el cliente**: el servidor antepone el prefijo del usuario autenticado a
  la entrada y lo quita a la salida, así watchers y web UI usan ids sin prefijo y no cambian.
- Se implementa en una **capa "datastore con alcance" (ScopedDatastore)** que envuelve el
  `Datastore` real: `buckets()` filtra+quita prefijo; `__getitem__`/`create_bucket`/etc. lo
  anteponen. Al scopear en el datastore, también quedan cubiertos `query2` y `export/import`.
- `admin` puede ver todos los espacios (con prefijo visible).
- Nota: exige forzar el prefijo de forma consistente en la capa scoped (única superficie a
  auditar) para evitar fugas entre usuarios.

### 4. Web UI / dashboards
- Por usuario: login con token → ve **solo sus datos** (su BD). Cambios mínimos (ya hay token).
- Admin (fase 2): selector de usuario + agregados entre usuarios (itera BDs por usuario).

### 5. Despliegue
- Servidor central en **Docker**, detrás de proxy TLS (Caddy/nginx). Clientes con
  `hostname=<central>` en `aw-client.toml`. Acceso restringido por VPN (WireGuard) o LAN.

## Cambios principales (mapa de implementación)
1. **Auth middleware**: nuevo módulo `aw_server/auth.py` + hook en `server.py:AWFlask` →
   resuelve `g.user`; `401` si falta/incorrecto.
2. **Registro de datastores por usuario**: en `AWFlask`/`ServerAPI`, sustituir el `Datastore`
   único (`server.py:60-61`) por resolución perezosa por `g.user`.
3. **Almacén de usuarios/tokens**: modelo + CLI para crear usuarios y emitir tokens
   (`aw-server` subcomando, p.ej. `aw-server users add <name>`), con hashing del token.
4. **Config**: nueva sección `[server] multiuser = true`, ruta de almacén de usuarios.
5. **Cliente**: documentar/soportar `hostname` remoto + token en `aw-client.toml`
   (ya sirve el Bearer; añadir carga de token remoto, hoy solo lee el de localhost).
6. **Web UI**: pantalla de login por token (mínimo) y, en fase 2, vista admin.
7. **Despliegue**: `Dockerfile` + `docker-compose.yml` + ejemplo de proxy TLS.

## Seguridad (a acordar)
- TLS obligatorio en tránsito (proxy). Tokens hasheados en reposo. Rotación/revocación.
- Consentimiento/aviso a empleados (especialmente con el watcher de screenshots).
- Límite de tamaño/*rate-limit* de ingesta.

## Fases de entrega
- **F1 (núcleo):** auth por token + BD por usuario + ingesta directa + CLI de usuarios.
- **F2 (operación):** login en web UI, Docker + proxy TLS, docs de despliegue.
- **F3 (admin):** dashboard agregado por usuario/equipo.
