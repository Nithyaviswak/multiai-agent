# Multi-Agent AI Network Automation System

Multi-agent AI system for network troubleshooting, configuration generation, and
compliance validation, built on FastAPI + LangGraph + Groq with a React frontend.
Runs against simulated Cisco environments (no hardware required).

> **Metrics honesty note:** Read [`backend/docs/METRICS.md`](backend/docs/METRICS.md).
> The previously advertised figures (95% task completion, 60% context reduction)
> were not backed by measurements and are **not claimed here**. Real, measured
> metrics from live Groq runs are documented in that file.

## Features

- **12 specialized agents** in a LangGraph pipeline:
  Planner, Topology Discovery, Knowledge, NETCONF Collection, Configuration,
  Automation, Verification, Monitoring, Compliance Checker, Log Analyzer,
  Incident Response, Report Generator.
- **Human-in-the-loop approval** — mutating actions pause for approval before any
  config is applied.
- **Failure-aware workflow** — bounded retries, failure routers, truthful
  terminal states (`complete` / `error` / `awaiting_approval` / `denied`).
- **Observability & cost tracking** — per-step trace with latency, tokens and
  estimated cost per run; queryable via API.
- **Guardrails** — deterministic input blocking, config allow-list, secret
  redaction (see [`backend/docs/SECURITY.md`](backend/docs/SECURITY.md)).
- **RBAC + audit logging** — permission checks and a full audit trail.
- **Rate limiting** — async token-bucket, per user.
- **Evaluation harness** — labeled dataset + deterministic scoring + optional
  live end-to-end runs (`backend/evaluate.py`).
- **Mock network tools**: NAPALM, Netmiko, Nornir, pyATS (simulated).

## Tech Stack

- **Backend:** FastAPI, LangGraph, LangChain, Groq, Pydantic v2
- **Frontend:** React, Vite, Tailwind, Framer Motion, Axios
- **Quality:** pytest suite, GitHub Actions CI, evaluation harness

## Project Structure

```text
multiai-agent/
  backend/
    app/
      agents/           # 12 LangGraph agents
      graph/            # LangGraph StateGraph workflow (retries, approvals, metrics)
      schemas/          # Pydantic models
      tools/
        network/        # Mock NAPALM, Netmiko, Nornir, pyATS
        guardrails/     # Input/output safety controls
        evaluation/     # Metric tracking
        rate_limiter.py # Async per-user rate limiter
        audit/          # Audit logging
        rbac/           # Permission checks
      data/             # Evaluation datasets
      config.py         # Settings + startup validation
      main.py           # FastAPI app + endpoints
    tests/              # pytest suite
    evaluate.py         # Evaluation harness
    docs/               # METRICS.md, SECURITY.md
    requirements.txt
  frontend/
    src/
      components/       # NetworkInput, AgentProgress, NetworkResults, EnterprisePanel
      hooks/
      services/         # NetworkAPI client
      pages/
    package.json
  .github/workflows/    # CI
  README.md
```

## Prerequisites

- Python 3.10+ (3.12 tested)
- Node.js 18+

## Environment Setup

```powershell
cd backend
Copy-Item .env.example .env
```

Set `GROQ_API_KEY` (and optionally `TAVILY_API_KEY`) in `backend/.env`.
The default `LLM_MODEL` is a model verified to exist on Groq
(`openai/gpt-oss-20b`); the app fails fast at startup if the configured model
is not on the known-good list.

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
.\venv\Scripts\python.exe -X utf8 -m pytest tests -q        # deterministic test suite
.\venv\Scripts\python.exe -X utf8 evaluate.py               # deterministic eval (no API)
.\venv\Scripts\python.exe -X utf8 evaluate.py --live        # full workflows (real API)
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | System info, available environments & devices |
| `POST` | `/api/network` | Start network automation workflow (rate-limited per user) |
| `GET` | `/api/network/{id}` | Get workflow status/result |
| `POST` | `/api/approve` | Approve/deny a paused mutation |
| `POST` | `/api/memory/history` | Conversation history (per session) |
| `POST` | `/api/memory/context` | Recent project context |
| `POST` | `/api/memory/undo` | Undo last config change |
| `GET` | `/api/evaluation/stats` | Per-agent + aggregate metrics |
| `GET` | `/api/runs/{run_id}` | Per-run trace + metrics |
| `GET` | `/api/audit/logs` | Audit log entries |
| `GET` | `/api/tools/call` | Invoke a registered tool |
| `GET` | `/api/tools/list` | List registered tools |
| `GET` | `/api/devices` | List all simulated devices |
| `GET` | `/api/topology` | Get network topology |
| `GET` | `/api/environments` | List available environments |
| `WS` | `/ws/{client_id}` | Real-time streaming |

### Example: Start Network Automation

```json
{
  "intent": "Configure OSPF on core-router-01",
  "environment": "devnet-sandbox",
  "user_id": "engineer"
}
```

## Example Intents

- `"Configure OSPF on core-router-01 and distribution-sw-01"`
- `"Verify BGP peering on edge-router-01"`
- `"Audit security compliance across all devices"`
- `"Troubleshoot connectivity issues between core and edge"`
- `"Generate VLAN configuration for distribution-sw-01"`
- `"Check logs on all devices for errors"`

## Workflow Pipeline

```
User Intent → Planner → Topology → Knowledge → NETCONF → Configuration →
Automation → Verification → Monitoring → Compliance → Log Analyzer →
Incident Response → [Approval Gate for mutations] → Report
```

## Mock Devices

| Hostname | Role | Vendor | Platform | Environment |
|----------|------|--------|----------|-------------|
| core-router-01 | Core | Cisco | IOS-XE 17.9.1 | DevNet Sandbox |
| edge-router-01 | Edge | Cisco | IOS-XE 17.6.3 | ContainerLab |
| distribution-sw-01 | Distribution | Cisco | IOS-XE 17.3.6 | GNS3 |
| access-sw-01 | Access | Cisco | IOS-XE 17.3.6 | EVE-NG |

## Security

See [`backend/docs/SECURITY.md`](backend/docs/SECURITY.md). Key points:

- Never commit real API keys; `backend/.env` is git-ignored.
- Mutating intents require human approval.
- Guardrails block destructive/credential-exfil inputs deterministically.

## Metrics & Evaluation

See [`backend/docs/METRICS.md`](backend/docs/METRICS.md) for how metrics are
collected and the honest, measured results.

## Deploy on Render

`render.yaml` deploys the backend from the `backend` directory. Required env
vars on Render:

- `GROQ_API_KEY`
- `TAVILY_API_KEY` (optional)
- `LLM_MODEL` (optional, default `openai/gpt-oss-20b`)

## Deploy Frontend on Netlify

`frontend/netlify.toml` pre-configures a proxy to the backend API.