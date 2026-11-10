#!/usr/bin/env bash
# One-time bootstrap for a fresh AWS EC2 instance (Ubuntu 22.04/24.04 or
# Amazon Linux 2023) that will host the app with Docker Compose.
#
# Usage (as root):
#   sudo REPO_URL=git@github.com:you/multiai-agent.git \
#        bash deploy/aws/setup-ec2.sh
#
# Optional environment:
#   APP_DIR=/opt/multiai-agent   where the repo is cloned
#   BRANCH=main                  branch to check out
set -euo pipefail

REPO_URL="${REPO_URL:-}"
APP_DIR="${APP_DIR:-/opt/multiai-agent}"
BRANCH="${BRANCH:-main}"
DEPLOY_USER="${SUDO_USER:-root}"

log() { printf '\n==> %s\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

if [ "$(id -u)" -ne 0 ]; then
    die "run as root: sudo REPO_URL=<git-url> bash deploy/aws/setup-ec2.sh"
fi

if [ -z "$REPO_URL" ] && [ ! -d "$APP_DIR/.git" ]; then
    die "REPO_URL is required when $APP_DIR is not already a git checkout, e.g. sudo REPO_URL=https://github.com/you/multiai-agent.git bash $0"
fi

if [ -f /etc/os-release ]; then
    . /etc/os-release
    log "Detected ${PRETTY_NAME:-unknown OS}"
fi

log "Installing base packages (git, curl, ca-certificates)"
if command -v apt-get >/dev/null 2>&1; then
    apt-get update -y
    DEBIAN_FRONTEND=noninteractive apt-get install -y git curl ca-certificates
elif command -v dnf >/dev/null 2>&1; then
    dnf install -y git curl ca-certificates
else
    yum install -y git curl ca-certificates
fi

if ! command -v docker >/dev/null 2>&1; then
    log "Installing Docker Engine + Compose plugin (get.docker.com)"
    curl -fsSL https://get.docker.com | sh
else
    log "Docker already installed; skipping installer"
fi

log "Enabling Docker at boot"
systemctl enable --now docker

docker --version
docker compose version >/dev/null 2>&1 || die "Docker Compose v2 plugin is missing"

if [ -d "$APP_DIR/.git" ]; then
    log "Repository already present at $APP_DIR (leaving it untouched)"
else
    log "Cloning $REPO_URL ($BRANCH) into $APP_DIR"
    mkdir -p "$(dirname "$APP_DIR")"
    git clone --branch "$BRANCH" --depth 1 "$REPO_URL" "$APP_DIR"
fi

log "Preparing backend environment file"
if [ ! -f "$APP_DIR/backend/.env" ]; then
    cp "$APP_DIR/backend/.env.example" "$APP_DIR/backend/.env"
    chmod 600 "$APP_DIR/backend/.env"
    echo "Created $APP_DIR/backend/.env"
fi

if [ "$DEPLOY_USER" != "root" ]; then
    log "Adding $DEPLOY_USER to the docker group"
    usermod -aG docker "$DEPLOY_USER" || true
fi

chown -R "$DEPLOY_USER":"$DEPLOY_USER" "$APP_DIR" 2>/dev/null || true

cat <<EOF

Bootstrap complete.

Next steps:
  1. Edit $APP_DIR/backend/.env and set GROQ_API_KEY (and any optional keys).
  2. Re-login (or run 'newgrp docker') so the docker group applies.
  3. Deploy:
       cd $APP_DIR
       bash deploy/aws/deploy.sh

Make sure the EC2 security group allows inbound TCP 22, 80 and 443 only.
Do not expose port 8000 publicly — nginx proxies the API inside the stack.
EOF
