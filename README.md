# Multi-AI-Agent Trip Planner

A provider-agnostic multi-agent travel-planning platform built on
FastAPI + LangGraph + LangChain with a React (Claude-style) frontend.

Specialized agents fetch real routes (car, bike, bus) from the free
OpenStreetMap data stack, estimate train corridors, find restaurants by meal
(tiffin / lunch / dinner), discover nearby places that fit your time budget,
and build a timed itinerary — using your own LLM keys and **no map API key**.

## Features

- **Bring your own key** — Groq / OpenAI / Anthropic keys, or register any
  **custom model by name + API key** (OpenRouter, Together, Ollama, etc.).
- **Free OpenStreetMap stack** — OpenFreeMap tiles + MapLibre on the map;
  Nominatim geocoding, OSRM road routing, Overpass POI search (Photon
  fallback). No Google Maps API key required, no simulated routes.
- **Dynamic origin/destination** — extracted from the request (no fixed city).
- **Per-mode route agents** — Car, Bus, Train, Bike compared deterministically.
- **Restaurants by meal** — tiffin (06–11), lunch (11–16), dinner (16–23),
  ranked by rating and distance from the route midpoint.
- **Places within budget** — feasibility pre-filtered so the itinerary never
  overflows the time budget.
- **Timed itinerary** — chronological stops with meal slots, place dwell times
  and detour estimates.
- **Model switching** — hot-swap the LLM from the UI composer.
- **Failure-aware workflow** — bounded retries, failure routers, truthful
  terminal states (`complete` / `error`).
- **Observability & cost tracking** — per-step trace with latency, tokens and
  estimated cost per run; queryable via API.
- **Guardrails** — deterministic input blocking, prompt-injection detection,
  secret redaction.
- **Rate limiting** — async token-bucket, per user.
- **Evaluation harness** — labeled dataset + deterministic extraction scoring
  + optional live end-to-end runs (`backend/evaluate.py`).
- **Ship-ready containers** — production Dockerfiles (non-root backend,
  multi-stage frontend served by nginx) plus a hot-reload dev Compose stack.
- **AWS deployment** — one-command EC2 bootstrap and repeatable deploy script
  for a single-host Docker Compose stack.

## Tech Stack

- **Backend:** FastAPI, LangGraph, LangChain, Groq, httpx, Pydantic v2
- **Frontend:** React, Vite, Tailwind, Framer Motion, Axios, MapLibre GL
- **Maps:** OpenFreeMap tiles · OSM data via Nominatim, OSRM, Overpass, Photon
- **Quality:** pytest (46 tests), evaluation harness
- **Deploy:** Docker, Docker Compose, nginx, AWS EC2

## Project Structure

```text
multiai-agent/
  backend/
    app/
      agents/           # TravelPlanner, 4 route agents, comparator, restaurants,
                        # places, itinerary, knowledge, report
      graph/            # LangGraph sequential workflow (retries, metrics)
      schemas/          # Pydantic models (AgentState, TravelRequest)
      tools/
        geo/            # Free OSM async client (routes, places, geocode)
        travel/         # meal_matcher, itinerary_builder (deterministic)
        guardrails/     # Input/output safety controls
        evaluation/     # Metric tracking
        rate_limiter.py # Async per-user rate limiter
        audit/          # Audit logging
      data/             # Evaluation datasets (eval_travel_dataset.json)
      config.py         # Settings + startup validation
      main.py           # FastAPI app + endpoints
    tests/              # 46 pytest tests (deterministic, no API keys needed)
    evaluate.py         # Evaluation harness
    requirements.txt
    Dockerfile          # production image (non-root, healthcheck)
    .dockerignore
  frontend/
    src/
      components/       # Composer, AgentProgress, TravelResults, Settings
      hooks/            # useTravelPlanner
      services/         # TravelAPI client
      pages/            # Dashboard
    package.json
    Dockerfile          # multi-stage build → nginx
    nginx.conf          # SPA fallback + /api and /ws reverse proxy
  deploy/aws/
    setup-ec2.sh        # one-time EC2 bootstrap (Docker, repo, env file)
    deploy.sh           # pull, build, restart, health-check
  docker-compose.yml    # production stack (frontend + backend)
  docker-compose.dev.yml # hot-reload development stack
  .github/workflows/    # CI + manual AWS EC2 deploy
  README.md
```

## Prerequisites

- Python 3.10+ (3.12 tested)
- Node.js 18+
- **No map API key needed** — map data comes from free public OpenStreetMap
  services (Nominatim, OSRM, Overpass, Photon, OpenFreeMap tiles).
- An LLM API key (Groq by default; OpenAI/Anthropic supported).

## Environment Setup

```powershell
cd backend
Copy-Item .env.example .env
```

Set `GROQ_API_KEY` in `backend/.env`. OpenAI, Anthropic and Tavily keys can
be added later from the UI or via env vars. Map endpoints are free defaults;
override `NOMINATIM_URL`, `OSRM_URL`, `OVERPASS_URL` and `PHOTON_URL` if you
self-host them. The default `LLM_MODEL` is `openai/gpt-oss-20b` (verified on
Groq); the app fails fast at startup if the model or a required key is missing.

## Run with Docker

The containers read the same `backend/.env` used by the manual setup, so
create it once (see above) and set `GROQ_API_KEY`. Python and Node are not
required on the host when using Docker.

### Development stack (hot reload)

```powershell
docker compose -f docker-compose.dev.yml up --build
```

- Frontend: `http://localhost:3000` (Vite dev server, live reload)
- Backend: `http://localhost:8000` (uvicorn `--reload`, source bind-mounted)

### Production stack (local smoke test)

```powershell
docker compose up -d --build
```

- App: `http://localhost` (nginx serves the built SPA and proxies `/api` + `/ws`)
- The backend is **not** published on a host port; only nginx is reachable.
- Change the public port with `FRONTEND_PORT`, e.g. on Linux/macOS:
  `FRONTEND_PORT=8080 docker compose up -d --build` (PowerShell:
  `$env:FRONTEND_PORT=8080; docker compose up -d --build`).

Useful commands:

```powershell
docker compose ps
docker compose logs -f backend
docker compose down          # stop and remove the stack
```

> **Scaling note:** workflow state, the key ring, the active model and rate
> limits live in process memory, so the backend intentionally runs a single
> uvicorn worker. Scale vertically (bigger instance) rather than adding
> replicas until that state is moved to a shared store.

## Run Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend URL: `http://localhost:8000`

## Run Frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend URL: `http://localhost:3000`

## Run Tests & Evaluation

```powershell
cd backend
.\venv\Scripts\python.exe -m pytest tests -q          # 46 deterministic tests
.\venv\Scripts\python.exe evaluate.py                  # deterministic eval (no API)
.\venv\Scripts\python.exe evaluate.py --live           # full workflows (needs keys)
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | System info (agents, modes, meals, tools, Maps status) |
| `POST` | `/api/travel` | Start travel workflow (rate-limited per user) |
| `GET` | `/api/travel/{id}` | Get workflow result |
| `GET` | `/api/maps/status` | Free OSM stack status (providers + endpoints) |
| `POST` | `/api/memory/history` | Conversation history (per session) |
| `POST` | `/api/memory/context` | Recent project context |
| `GET` | `/api/evaluation/stats` | Per-agent + aggregate metrics |
| `GET` | `/api/models` | List supported models |
| `GET` | `/api/models/current` | Currently active model |
| `POST` | `/api/models` | Switch the active model |
| `POST` | `/api/models/custom` | Register a custom model |
| `DELETE` | `/api/models/custom` | Remove a custom model |
| `POST` | `/api/models/keys` | Set/update an API key for a model |
| `GET` | `/api/models/base-urls` | Preset OpenAI-compatible base URLs |
| `GET` | `/api/providers` | Provider/key status |
| `POST` | `/api/providers/keys` | Save a provider API key |
| `GET` | `/api/runs/{run_id}` | Per-run trace + metrics |
| `GET` | `/api/audit/logs` | Audit log entries |
| `POST` | `/api/tools/call` | Invoke a registered tool |
| `GET` | `/api/tools/list` | List registered tools |
| `WS` | `/ws/{client_id}` | Real-time streaming |

### Example: Start Travel Workflow

```json
{
  "intent": "Plan a trip from Bengaluru to Mysuru by train with lunch and places to cover within 6 hours",
  "origin": "Bengaluru",
  "destination": "Mysuru",
  "travel_modes": ["train"],
  "meal_types": ["lunch"],
  "time_budget_minutes": 360
}
```

All fields except `intent` are optional — the planner agent extracts them
from the natural-language request.

## Workflow Pipeline

```
User Intent
  → Travel Planner (extract origin, destination, modes, meals, budget)
  → Car / Bus / Train / Bike routes (OSM stack: OSRM roads + estimates)
  → Route Comparator (best mode by budget + speed)
  → Gather Knowledge / Find Restaurants / Find Places (sequential)
  → Build Itinerary (deterministic greedy scheduler)
  → Generate Report (structured summary)
  → Complete
```

## Map data — how it works & honest limitations

The stack is fully keyless and uses shared public services, so be a good
citizen: keep request volume modest (Nominatim is throttled to ~1 req/s
with a custom User-Agent; Overpass is best served with single batched
queries, which the places agent already does).

| Capability | Source | Notes |
|------------|--------|-------|
| Geocoding | Nominatim | ~1 req/s throttle, custom User-Agent |
| Car routes | OSRM (driving) | Real road route + road shape |
| Bike routes | OSRM (cycling) | Public demo router **currently mirrors driving data** — treat bike distance/time as a road-network approximation |
| Bus routes | OSRM (driving × 1.45) | Driving shape with transit-scaled time (estimate) |
| Train routes | Great-circle corridor | **Estimate**: ~62 km/h, ×1.15 detour; no free transit feed |
| Restaurants/places | Overpass (OSM tags) | Batched to one query per search |
| Free-text place search | Photon (komoot) | Fallback when no OSM tag matches |
| Map tiles | OpenFreeMap (MapLibre) | Theme-aware positron (light) / dark (dark) |

No live opening hours or live transit departures are used; `depart_at` is
accepted for API compatibility and ignored. If a public service is down or
rate-limited, the affected agent reports a truthful "maps unavailable" state.

## Security

- Never commit real API keys; `backend/.env` is git-ignored.
- Keys live in in-memory keyring only; providers without a key are not
  offered in the model picker.
- Guardrails block destructive / prompt-injection inputs deterministically.
- Output sanitizer redacts `api_key`, `password`, `secret`, `token` patterns.

## Deploy on AWS EC2 (Docker Compose)

Recommended single-host AWS setup: one EC2 instance runs the production
Compose stack. The frontend container's nginx serves the SPA and reverse
proxies `/api` and `/ws` to the backend container, so the only public port is
80/443. No ALB, ECS, RDS or other managed services are required — the app has
no persistent server-side data.

| AWS service | Role in this setup |
|-------------|--------------------|
| **EC2** | Runs the Docker Compose stack |
| **EBS** (gp3) | OS, images and build cache |
| **Elastic IP** | Stable public address across restarts |
| **Security group** | Ingress for 22, 80 and 443 only |
| *Optional:* ALB + ACM | HTTPS termination |
| *Optional:* CloudWatch | Ship container metrics/logs with the CloudWatch agent |
| *Optional:* SSM Parameter Store / Secrets Manager | Deliver `GROQ_API_KEY` without a local file |

### 1. Launch the instance

| Setting | Value |
|---------|-------|
| AMI | Ubuntu 24.04 LTS (Amazon Linux 2023 also works) |
| Instance type | `t3.medium` recommended (comfortable image builds); `t3.small` works for demos |
| Storage | 20–30 GB gp3 |
| Security group — inbound | TCP 22 from your IP, TCP 80 and 443 from `0.0.0.0/0` |
| Security group — inbound | **Do not open 8000** — the API is only reachable through nginx |
| Elastic IP | Recommended, so the address survives instance restarts |

An IAM role with SSM Session Manager is optional but lets you shell in without
exposing port 22.

### 2. Bootstrap the host

```bash
ssh ubuntu@<elastic-ip>

# Get the repository onto the instance (HTTPS or a deploy key for private repos)
sudo apt-get update && sudo apt-get install -y git
sudo git clone https://github.com/<you>/<repo>.git /opt/multiai-agent

# Install Docker + Compose plugin, create backend/.env, fix ownership
sudo bash /opt/multiai-agent/deploy/aws/setup-ec2.sh
```

`setup-ec2.sh` installs Docker from get.docker.com, enables it at boot, adds
your login user to the `docker` group, and creates
`/opt/multiai-agent/backend/.env` from `.env.example` (mode `600`).

If the repo is not cloned yet, pass it explicitly instead:

```bash
sudo REPO_URL=https://github.com/<you>/<repo>.git \
  bash deploy/aws/setup-ec2.sh
```

### 3. Configure secrets

```bash
sudo nano /opt/multiai-agent/backend/.env
```

At minimum set:

```dotenv
GROQ_API_KEY=gsk_...
```

`TAVILY_API_KEY` is optional. The OSM endpoints default to the free public
services and need no key. Keep the file owned by your deploy user, mode `600`:

```bash
sudo chown "$USER":"$USER" /opt/multiai-agent/backend/.env
sudo chmod 600 /opt/multiai-agent/backend/.env
```

> Never commit `.env`. For stricter setups, load secrets from AWS SSM
> Parameter Store or Secrets Manager into the file in your deploy pipeline.

### 4. Deploy

Log out and back in (or run `newgrp docker`) so the docker group applies, then:

```bash
cd /opt/multiai-agent
bash deploy/aws/deploy.sh
```

The deploy script:

1. pulls the configured branch (`BRANCH`, default `main`),
2. builds both images with `--pull`,
3. recreates the stack with `up -d --remove-orphans`,
4. waits for `http://127.0.0.1/healthz` and prints `docker compose ps`.

Run the same command for every later deploy; it is idempotent.

### 5. Verify

```bash
curl http://localhost/healthz        # -> ok
curl http://localhost/api/maps/status
```

Then open `http://<elastic-ip>/` in a browser. The app and API share the same
origin, so no CORS configuration is needed.

### 6. HTTPS

Terminate TLS in front of the instance, for example:

- an **Application Load Balancer** with an ACM certificate forwarding 443 → 80, or
- **CloudFront** with the instance as origin (and 80/443 restricted to the
  CloudFront/ALB security group), or
- **Caddy** on the host as a reverse proxy with automatic Let's Encrypt certs.

Keep the security group limited to the proxy/load balancer once TLS is in
place.

### Updating and operating the stack

Run these from `/opt/multiai-agent`:

```bash
bash deploy/aws/deploy.sh                     # pull + rebuild + restart
docker compose ps                             # service status
docker compose logs -f backend                # follow backend logs
docker compose restart backend                # restart one service
docker compose down                           # stop the stack
docker system df                              # disk usage
docker image prune -f                         # remove dangling images
```

Containers use `restart: unless-stopped` and Docker is enabled at boot, so the
stack comes back automatically after an instance reboot.

### Optional: deploy from GitHub Actions

`.github/workflows/deploy-aws.yml` is a manual (`workflow_dispatch`) workflow
that SSHes into the instance and runs `deploy/aws/deploy.sh`. Add these
repository secrets:

| Secret | Purpose |
|--------|---------|
| `EC2_HOST` | Elastic IP or DNS name |
| `EC2_USER` | `ubuntu` (or `ec2-user` on Amazon Linux) |
| `EC2_SSH_KEY` | Private key whose public half is in `~/.ssh/authorized_keys` |
| `EC2_APP_DIR` | Optional, defaults to `/opt/multiai-agent` |

The SSH user must be in the `docker` group (done by `setup-ec2.sh`).

### Single-host caveats

- **State is in memory.** In-flight workflows, API keys added through the UI,
  the active model and rate-limit buckets are lost on restart. Keys from
  `backend/.env` are re-applied at boot.
- **One backend process.** Do not add replicas or `--workers > 1`; that would
  split in-memory state across processes. Scale the instance vertically.
- **The instance is the persistence.** Back up `backend/.env` (or keep it in a
  secret manager) and optionally snapshot the EBS volume.
- For multi-AZ or autoscaling requirements, move workflow/key state to a shared
  store (e.g. ElastiCache/Postgres) before moving to ECS or multiple instances.
