# Deploying the CEPEM Watch central server

Runs the Python `aw-server` in **multi-user mode** (per-user token auth + data
isolation) in Docker, behind Caddy for automatic HTTPS. See
[`../MULTIUSER_DESIGN.md`](../MULTIUSER_DESIGN.md) for the architecture.

## 1. Bring up the server

From the repository root (the Docker build needs the submodules checked out):

```bash
cd deploy
CEPEM_DOMAIN=watch.cepem.example docker compose up -d --build
```

- Point `watch.cepem.example`'s DNS at this host and open ports 80/443; Caddy
  provisions and renews a Let's Encrypt certificate automatically.
- For a LAN/VPN-only deployment without TLS, comment out the `caddy` service and
  publish `5600` directly (see `docker-compose.yml`), ideally over WireGuard.

## 2. Create users (issue tokens)

Tokens are printed once and stored only as a hash.

```bash
docker compose exec cepem-watch python -m aw_server.authcli add alice
docker compose exec cepem-watch python -m aw_server.authcli add admin --admin
docker compose exec cepem-watch python -m aw_server.authcli list
# rotate / remove:
docker compose exec cepem-watch python -m aw_server.authcli reissue alice
docker compose exec cepem-watch python -m aw_server.authcli revoke alice
```

## 3. Configure each employee's machine

Point the client at the central server and set its token in `aw-client.toml`
(`%LOCALAPPDATA%\cepemwatch\cepemwatch\aw-client\aw-client.toml` on Windows,
`~/.config/cepemwatch/aw-client/aw-client.toml` on Linux):

```toml
[server]
hostname = "watch.cepem.example"
port = "443"
api_key = "<the token printed by 'authcli add'>"
```

The watchers (window/AFK/screenshots) then send directly to the central server,
authenticated with the token; each user's data is fully isolated.

## 4. Web dashboard

Open `https://watch.cepem.example/` and paste the token on the login screen. The
UI stores it for the session and shows only that user's data. A 401 sends the
user back to the login screen; use "Cerrar sesión" to switch users.

## Data & backups

Named volumes hold state:
- `cw-data` — the event database (`/data/cepemwatch/...`)
- `cw-config` — `users.json` (tokens) and server config (`/config/cepemwatch/...`)
- `cw-cache` — logs

Back up `cw-data` and `cw-config` regularly.
