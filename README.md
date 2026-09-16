# Multi-AI-Agent Trip Planner

A provider-agnostic multi-agent travel-planning platform built on
FastAPI + LangGraph + LangChain with a React (Claude-style) frontend.

Specialized agents fetch real Google Maps routes (car, bus, train, bike),
find restaurants by meal (tiffin / lunch / dinner), discover nearby places
that fit your time budget, and build a timed itinerary — using your own
LLM keys and a Google Maps API key.

## Features

- **Bring your own key** — Groq / OpenAI / Anthropic keys, or register any
  **custom model by name + API key** (OpenRouter, Together, Ollama, etc.).
- **Google Maps integration** — real Directions + Places data; no simulated routes.
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

## Tech Stack

- **Backend:** FastAPI, LangGraph, LangChain, Groq, httpx, Pydantic v2
- **Frontend:** React, Vite, Tailwind, Framer Motion, Axios
- **Maps:** Google Maps Directions + Places APIs
- **Quality:** pytest (46 tests), evaluation harness

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
        geo/            # Google Maps async client (directions, places, geocode)
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
  frontend/
    src/
      components/       # Composer, AgentProgress, TravelResults, Settings
      hooks/            # useTravelPlanner
      services/         # TravelAPI client
      pages/            # Dashboard
    package.json
  render.yaml           # Render deployment
  docker-compose.yml    # Docker Compose (backend + frontend)
  README.md
```

## Prerequisites

- Python 3.10+ (3.12 tested)
- Node.js 18+
- A [Google Maps API key](https://console.cloud.google.com/apis/credentials)
  with **Directions API** and **Places API** enabled.

## Environment Setup

```powershell
cd backend
Copy-Item .env.example .env
```

Set `GROQ_API_KEY` and `GOOGLE_MAPS_API_KEY` in `backend/.env`. OpenAI,
Anthropic and Tavily keys can be added later from the UI or via env vars.
The default `LLM_MODEL` is `openai/gpt-oss-20b` (verified on Groq); the app
fails fast at startup if the model or a required key is missing.

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
| `GET` | `/api/maps/status` | Whether a Google Maps API key is configured |
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
  → Car / Bus / Train / Bike routes (Google Maps Directions API, sequential)
  → Route Comparator (best mode by budget + speed)
  → Gather Knowledge / Find Restaurants / Find Places (sequential)
  → Build Itinerary (deterministic greedy scheduler)
  → Generate Report (structured summary)
  → Complete
```

## Security

- Never commit real API keys; `backend/.env` is git-ignored.
- Keys live in in-memory keyring only; providers without a key are not
  offered in the model picker.
- Guardrails block destructive / prompt-injection inputs deterministically.
- Output sanitizer redacts `api_key`, `password`, `secret`, `token` patterns.

## Deploy on Render

`render.yaml` deploys the backend from the `backend` directory. Required env
vars on Render:

- `GROQ_API_KEY` (default LLM provider)
- `GOOGLE_MAPS_API_KEY` (required for real route/place data)
- `TAVILY_API_KEY` (optional — adds web travel tips when configured)
- `LLM_MODEL` (optional, default `openai/gpt-oss-20b`)

## Deploy Frontend on Netlify

`frontend/netlify.toml` pre-configures a proxy to the backend API.