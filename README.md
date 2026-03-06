# Multi-Agent AI Research System

Production-style full-stack app for AI-assisted research, summarization, report writing, fact-checking, and PDF export.

## Features

- FastAPI backend with LangGraph multi-agent workflow
- React + Vite frontend with live workflow polling
- Agents for:
  - Research
  - Summarization
  - Report Writing
  - Fact Checking
- PDF generation endpoint for completed reports
- Rate limiting and structured logging

## Tech Stack

- Backend: FastAPI, LangGraph, LangChain, Groq, Tavily, Pydantic
- Frontend: React, Vite, Tailwind, Framer Motion, Axios

## Project Structure

```text
multiai-agent/
  backend/
    app/
    .env.example
    requirements.txt
  frontend/
    src/
    package.json
  .gitignore
```

## Prerequisites

- Python 3.10+ (3.12 tested)
- Node.js 18+
- npm

## Environment Setup

1. Create backend env file from example:

```powershell
cd backend
Copy-Item .env.example .env
```

2. Set your keys in `backend/.env`:

- `GROQ_API_KEY`
- `TAVILY_API_KEY`

Default model is:

- `LLM_MODEL=llama-3.1-8b-instant`

## Run Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend URL: `http://localhost:8000`

## Run Frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend URL: `http://localhost:3000`

The frontend proxies `/api` to backend port `8000`.

## API Endpoints

- `GET /` - health message
- `POST /api/research` - start workflow
- `GET /api/research/{workflow_id}` - get workflow status/result
- `POST /api/generate-pdf/{workflow_id}` - generate report PDF

### Example: Start Research

```json
{
  "topic": "AI trends in 2026",
  "max_retries": 3
}
```

## Common Issues

- `model_decommissioned` from Groq:
  - Set `LLM_MODEL` to a supported model (default here is `llama-3.1-8b-instant`).

- Backend startup error: `Extra inputs are not permitted`:
  - Remove unknown keys from `.env` (for example `python=3.12`).

- Frontend timeout:
  - Verify backend is running on port `8000`.
  - Check backend logs for agent errors.

## Security Notes

- Never commit real API keys.
- Keep `backend/.env` ignored.
- If keys were exposed, rotate them immediately.

## Deploy on Render

This repo now includes `render.yaml`, which runs the web service from `backend/` so `app.main:app` resolves correctly.

If configuring manually in the Render dashboard, use:

- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`

Required env vars on Render:

- `GROQ_API_KEY`
- `TAVILY_API_KEY`
- Optional: `LLM_MODEL` (default `llama-3.1-8b-instant`)
