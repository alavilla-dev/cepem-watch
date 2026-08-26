# syntax=docker/dockerfile:1
#
# CEPEM Watch central server (Python aw-server, multi-user mode).
#
# The web UI is expected to be PRE-BUILT into aw-server/aw_server/static (this is
# what the normal `make build` / `make -C aw-server aw-webui` and CI already do).
# Building the Vue UI inside the image is intentionally avoided: it needs Node and
# is memory-heavy/flaky in some Docker environments. deploy/build-image.sh builds
# the UI first, then this image.
#
# Build context MUST be the repository root:
#   bash deploy/build-image.sh                # builds UI + image
#   # or, if the UI is already built:
#   docker build -f deploy/Dockerfile -t cepem-watch-server .
#
# Uses the LOCAL forked aw-core/aw-client (data dir "cepemwatch", remote api_key
# support) instead of the upstream PyPI packages.

FROM python:3.9-slim-bookworm AS server
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    XDG_DATA_HOME=/data \
    XDG_CONFIG_HOME=/config \
    XDG_CACHE_HOME=/cache
WORKDIR /app

# Install the forked core libs first, then the server (its aw-core/aw-client
# requirements are already satisfied by these local installs).
COPY aw-core/ ./aw-core/
COPY aw-client/ ./aw-client/
# Pin peewee to 3.x: peewee 4.x returns DateTimeField values as datetime objects,
# which breaks aw-datastore's iso8601.parse_date(self.created) (upstream expects a
# string). The bundle's lockfile pins 3.x for the same reason.
RUN pip install 'peewee>=3.16,<4' ./aw-core ./aw-client

COPY aw-server/ ./aw-server/
# The webui submodule source isn't needed at runtime; the built bundle lives in
# aw_server/static and is packaged by aw-server's `include`.
RUN rm -rf ./aw-server/aw-webui \
    && test -f ./aw-server/aw_server/static/index.html \
        || (echo "ERROR: web UI not built (aw_server/static/index.html missing). Run deploy/build-image.sh or 'make -C aw-server aw-webui' first." && exit 1)
RUN pip install ./aw-server

# Event DB (/data), users.json + config (/config), logs (/cache) as volumes.
VOLUME ["/data", "/config", "/cache"]
EXPOSE 5600

# Multi-user mode; bind all interfaces (put a TLS reverse proxy in front).
CMD ["aw-server", "--multiuser", "--host", "0.0.0.0", "--port", "5600"]
