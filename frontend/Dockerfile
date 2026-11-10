# ── Build stage ──────────────────────────────────────────────────
FROM node:20-alpine AS build

WORKDIR /app

# Install dependencies from the lockfile first for better layer caching.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# ── Runtime stage ────────────────────────────────────────────────
FROM nginx:1.27-alpine AS runtime

# SPA + reverse proxy for the backend API and WebSocket.
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://127.0.0.1/healthz >/dev/null || exit 1
