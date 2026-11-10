#!/usr/bin/env bash
# Build and (re)start the production Docker Compose stack.
# Safe to run repeatedly for deploys, restarts and roll-forwards.
#
# Usage:
#   cd /opt/multiai-agent
#   bash deploy/aws/deploy.sh
#
# Optional environment:
#   APP_DIR=/opt/multiai-agent     repository location
#   BRANCH=main                    branch to pull before building
#   COMPOSE_FILE=docker-compose.yml
#   FRONTEND_PORT=80               host port published by the frontend
#   HEALTH_URL=http://127.0.0.1/healthz
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/multiai-agent}"
BRANCH="${BRANCH:-main}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
FRONTEND_PORT="${FRONTEND_PORT:-80}"

if [ "$FRONTEND_PORT" = "80" ]; then
    HEALTH_URL="${HEALTH_URL:-http://127.0.0.1/healthz}"
else
    HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:${FRONTEND_PORT}/healthz}"
fi

log() { printf '\n==> %s\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

cd "$APP_DIR" || die "APP_DIR $APP_DIR does not exist"

command -v docker >/dev/null 2>&1 || die "docker is not installed (run setup-ec2.sh first)"
docker compose version >/dev/null 2>&1 || die "docker compose v2 plugin is missing"
docker info >/dev/null 2>&1 || die "cannot talk to the Docker daemon (add your user to the docker group or use sudo)"

[ -f "$COMPOSE_FILE" ] || die "$COMPOSE_FILE not found in $APP_DIR"
[ -f backend/.env ] || die "backend/.env is missing — copy backend/.env.example and set GROQ_API_KEY"

if grep -Eq '^[[:space:]]*GROQ_API_KEY[[:space:]]*=[[:space:]]*($|your_)' backend/.env; then
    die "GROQ_API_KEY is empty in backend/.env — set a real key before deploying"
fi

if [ -d .git ]; then
    log "Updating source from origin/$BRANCH"
    git fetch --prune origin "$BRANCH"
    git checkout "$BRANCH"
    git pull --ff-only origin "$BRANCH"
else
    log "No .git directory found; deploying the files already present"
fi

log "Building images"
docker compose -f "$COMPOSE_FILE" build --pull

log "Starting stack"
docker compose -f "$COMPOSE_FILE" up -d --remove-orphans

# Drop dangling images from previous builds. Running containers are untouched.
docker image prune -f >/dev/null 2>&1 || true

log "Waiting for $HEALTH_URL"
healthy=0
for _ in $(seq 1 30); do
    if curl -fsS --max-time 3 "$HEALTH_URL" >/dev/null 2>&1; then
        healthy=1
        break
    fi
    sleep 2
done

if [ "$healthy" -ne 1 ]; then
    echo
    docker compose -f "$COMPOSE_FILE" ps || true
    echo
    docker compose -f "$COMPOSE_FILE" logs --tail=100 || true
    die "stack did not become healthy at $HEALTH_URL"
fi

log "Stack is healthy"
docker compose -f "$COMPOSE_FILE" ps
