# Security

This document describes the security model of the Multi-Agent AI Network
Automation Platform. It is a living document; update it whenever security
controls change.

## Threat model

The platform is designed for a lab / sandbox context (simulated devices), but it
contains the controls needed before connecting to real network gear:

- Users vs operators are distinct personas (`RBAC`).
- Intent comes from an untrusted conversational input and must not be able to
  trigger arbitrary mutations.
- LLM output is untrusted and must not be able to fabricate device targets,
  dangerous commands, or leak credentials.

## Controls

### 1. Input guardrails (deterministic)

`app/tools/guardrails/__init__.py` enforces, on every `/api/network` request:

- **Blocked patterns** for destructive system-wide operations (`rm -rf /`,
  `erase flash`, `drop table`, credential exfiltration such as
  `recover password for ...`, `send credentials to ...`, broad privilege grants).
- **Config command allow-list** (`validate_config`) that rejects unknown or
  destructive directives.
- **Device allow-list** (`validate_target_devices`) that flags targets not in the
  known inventory, catching LLM-hallucinated hostnames.

These checks are regex / allow-list based and never delegate the safety decision
to the LLM, so they are deterministic, auditable and testable.

### 2. Human approval for mutating actions

Actions classified as `configure`, `push`, or `delete` pause at the approval
gate (`terminal_status="awaiting_approval"`) and require an explicit
`POST /api/approve` before any config is applied to devices.

### 3. RBAC

`app/tools/rbac/__init__.py` gates the approve endpoint: a user must hold the
`configure` permission, otherwise `403`.

### 4. Secret redaction

`guardrails.sanitize_output` redacts `api_key`, `password`, `secret`, `token`,
AWS/GROQ/TAVILY keys, etc. from any output before it is shown to the user.

Credentials live only in `backend/.env` (git-ignored). `.env.example` documents
the variables with placeholders. Never commit real keys.

### 5. Rate limiting (per user)

`app/tools/rate_limiter.py` provides an async token-bucket limiter keyed by
`user_id`. Exceeding the limit returns `429`. Limits are configured in
`backend/.env` (`RATE_LIMIT_REQUESTS`, `RATE_LIMIT_WINDOW`).

### 6. Failure containment

The workflow retries each agent step a bounded number of times
(`MAX_RETRIES`), routes failures to a terminal `error` state, and never returns
partial work as success. Approvals can only resume from the exact pausing state.

### 7. Logging & audit

- Structured logging via `app/logging_config.py` (no secrets are logged).
- `app/tools/audit` records who did what, on which resource, and the outcome.

## Secrets checklist

- [ ] Keep `backend/.env` out of version control (it is git-ignored).
- [ ] Rotate the Groq API key if it is ever committed or exposed.
- [ ] Do not add new secret literals to code or docs; use settings + `.env`.

## Reporting issues

Open a GitHub issue on this repository. Do not include secrets in reports.