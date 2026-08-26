#!/usr/bin/env bash
# Build the CEPEM Watch central-server image: web UI (on host, needs Node+make)
# then the Docker image (copies the pre-built UI). Run from anywhere.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/.." && pwd)"

echo ">> Building web UI (Node + make required)..."
make -C "$root/aw-server" aw-webui

echo ">> Building Docker image cepem-watch-server:latest ..."
docker build -f "$root/deploy/Dockerfile" -t cepem-watch-server:latest "$root"

echo ">> Done. Run with: cd deploy && docker compose up -d"
