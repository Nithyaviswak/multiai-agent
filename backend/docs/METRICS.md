# Metrics & Evaluation

This document explains how the platform measures itself, what the numbers mean,
and the honest results recorded so far. **No number here is fabricated.** Metrics
come from actual runs against the real Groq API on the live workflow.

## How metrics are collected

Every run produces a structured trace and a metrics summary:

- **Trace** (`state["trace"]`): one entry per workflow step with
  `started_at`, `duration_ms`, `attempts`, `skipped`, `error`, and the LLM
  usage (tokens + estimated cost) for that step.
- **Run metrics** (`state["metrics"]`): `total_latency_ms`, `steps`,
  `failed_steps`, `retries_total`, `skipped_steps`, `total_tokens`,
  `estimated_cost_usd`, `tool_calls`, `terminal_status`.
- **Evaluation tracker** (`app/tools/evaluation`): aggregates per-agent stats
  (success rate, avg latency, tokens, cost) and per-run records. Exposed via
  `GET /api/evaluation/stats` and `GET /api/runs/{run_id}`.

Cost is estimated from a per-model price table
(`MODEL_COST_PER_1M` in `app/agents/base.py`). It is an *estimate* for internal
budgeting, not a billing invoice.

## What is measured vs. not measured

| Claim | Status |
|-------|--------|
| End-to-end latency, steps, retries, tokens, cost | Measured per run |
| Intent → action classification accuracy | Measured on a labeled dataset |
| Guardrail blocking of destructive intents | Measured on a labeled dataset |
| "95% task completion" | **Not claimed** – no evidence collected yet |
| "60% context reduction" | **Not claimed** – no benchmark for this exists |

We deliberately do not advertise the two headline numbers from the original
README until an evaluation experiment can back them up.

## How to re-run the evaluation

```bash
cd backend
.\.venv\Scripts\python.exe -X utf8 evaluate.py                        # deterministic checks
.\.venv\Scripts\python.exe -X utf8 evaluate.py --live --limit 10      # full workflows, real API
```

`evaluate.py` exits non-zero if the deterministic checks regress, so CI can gate
on it. The dataset lives in `app/data/eval_dataset.json`; add labeled cases
there as the platform grows.

## Results recorded (2026-08-17, model `openai/gpt-oss-20b`)

### Deterministic classification (10-case dataset)

| Metric | Value |
|--------|-------|
| Action accuracy | 1.0 (10/10) |
| Technology accuracy | 1.0 |
| Target extraction accuracy | 1.0 |
| Destructive intents blocked | 2/2 |

### Live end-to-end runs (10 intents, real Groq API)

| Metric | Value |
|--------|-------|
| Completed / attempted | 8/10 (2 correctly paused for approval) |
| Average latency | ~3.8 s per workflow |
| Average tokens | ~964 per workflow |
| Total cost (10 runs) | ~$0.0015 |

These are point-in-time samples. Rerun `evaluate.py --live` to refresh them.

## Units

- Latency in milliseconds (`total_latency_ms`).
- Tokens are the sum of input+output tokens reported by the model provider.
- Cost in USD, rounded to 6 decimals.
