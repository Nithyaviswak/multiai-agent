from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import json
import uuid
from app.graph.workflow import travel_workflow
from app.logging_config import logger
from app.config import settings, validate_settings, validate_optional
from app.tools.rate_limiter import rate_limiter
from app.tools.memory import conversation_memory, project_memory
from app.tools.audit import audit_logger
from app.tools.evaluation import evaluation
from app.tools.guardrails import guardrails
from app.tools.calling.registry import tool_registry
from app.tools.model_registry import (
    list_models, get_model, register_custom_model, unregister_custom_model,
    list_base_urls,
)
from app.tools.keyring import keyring
from app.tools.geo.maps_client import maps_client

app = FastAPI(
    title="Multi-Agent AI Travelling Agent",
    description="Multi-agent travel planner: per-mode route agents (car, bus, train, bike), restaurant lookup by meal (tiffin, lunch, dinner), place discovery within a time budget, and a timed itinerary builder. Real Google Maps Directions + Places data.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request/Response Models ─────────────────────────────────────
class TravelRequest(BaseModel):
    intent: str
    origin: Optional[str] = None
    destination: Optional[str] = None
    travel_modes: Optional[List[str]] = None
    meal_types: Optional[List[str]] = None
    time_budget_minutes: Optional[int] = None
    preferences: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = "default"
    user_id: Optional[str] = "engineer"

class TravelResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]]
    error: Optional[str]
    workflow_id: Optional[str]

class MemoryQuery(BaseModel):
    session_id: str

class ToolCallRequest(BaseModel):
    tool: str
    params: Dict[str, Any]

class ModelRequest(BaseModel):
    model: str

class ProviderKeyRequest(BaseModel):
    provider: str
    key: str

class CustomModelRequest(BaseModel):
    name: str
    model_id: str
    api_key: str = ""
    base_url: str = ""

class ModelKeyRequest(BaseModel):
    model_id: str
    api_key: str

# ── Global workflow state ─────────────────────────────────────────
workflow_state = {}

def _prune_workflow_state():
    """Keep in-memory workflow state bounded (LRU-ish eviction of oldest runs)."""
    if len(workflow_state) > settings.MAX_WORKFLOW_STATE_ENTRIES:
        evict = len(workflow_state) - settings.MAX_WORKFLOW_STATE_ENTRIES
        for k in list(workflow_state)[:evict]:
            workflow_state.pop(k, None)

# Active LLM model (defaults to the configured model; can be changed at runtime).
active_model = settings.LLM_MODEL

def _apply_active_model() -> None:
    """Push the active model to every agent in the running workflow."""
    travel_workflow.set_model(active_model)

# ── WebSocket Connections ────────────────────────────────────────
active_connections: Dict[str, WebSocket] = {}

# ── Root ─────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "message": "Multi-Agent AI Travelling Agent",
        "version": "1.0.0",
        "agents": ["TravelPlanner", "CarRoute", "BusRoute", "TrainRoute", "BikeRoute",
                    "RouteComparator", "Knowledge", "Restaurant", "Places",
                    "Itinerary", "ReportGenerator"],
        "travel_modes": ["car", "bus", "train", "bike"],
        "meal_types": ["tiffin", "lunch", "dinner"],
        "tools": [t["name"] for t in tool_registry.list_tools()],
        "features": ["tool_calling", "memory", "audit_logging",
                      "evaluation", "guardrails", "websockets", "google_maps"],
        "maps_configured": maps_client.has_credentials(),
    }

# ── Workflow Endpoints ───────────────────────────────────────────
@app.post("/api/travel", response_model=TravelResponse)
async def start_travel_workflow(request: TravelRequest, background_tasks: BackgroundTasks):
    try:
        if not await rate_limiter.check_limit(request.user_id):
            raise HTTPException(status_code=429, detail="Rate limit exceeded, try again later")

        if not request.intent.strip():
            raise HTTPException(status_code=400, detail="Travel intent is required")

        guard_check = guardrails.validate_input(request.intent)
        if not guard_check["safe"]:
            raise HTTPException(status_code=400, detail=f"Input blocked: {guard_check['issues']}")

        workflow_id = str(uuid.uuid4())

        workflow_state[workflow_id] = {
            "workflow_id": workflow_id,
            "intent": request.intent,
            "origin": request.origin,
            "destination": request.destination,
            "travel_modes": request.travel_modes,
            "meal_types": request.meal_types,
            "time_budget_minutes": request.time_budget_minutes,
            "session_id": request.session_id,
            "user_id": request.user_id,
            "current_step": "plan",
            "status": "running",
        }

        background_tasks.add_task(
            run_workflow, workflow_id,
            intent=request.intent, origin=request.origin, destination=request.destination,
            travel_modes=request.travel_modes, meal_types=request.meal_types,
            time_budget_minutes=request.time_budget_minutes, preferences=request.preferences,
            session_id=request.session_id, user_id=request.user_id,
        )

        audit_logger.log("workflow_started", request.user_id, "workflow",
                         {"intent": request.intent, "id": workflow_id})
        _prune_workflow_state()

        return TravelResponse(
            success=True,
            data={"workflow_id": workflow_id, "status": "started"},
            error=None,
            workflow_id=workflow_id,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("API endpoint error", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/travel/{workflow_id}")
async def get_travel_result(workflow_id: str):
    if workflow_id not in workflow_state:
        raise HTTPException(status_code=404, detail="Workflow not found")
    result = workflow_state[workflow_id]
    if "error" in result and isinstance(result.get("error"), str):
        return TravelResponse(success=False, data=None, error=result["error"], workflow_id=workflow_id)
    return TravelResponse(success=True, data=result, error=None, workflow_id=workflow_id)

# ── Memory Endpoints ─────────────────────────────────────────────
@app.post("/api/memory/history")
async def get_conversation_history(req: MemoryQuery):
    history = conversation_memory.get_history(req.session_id)
    return {"success": True, "session_id": req.session_id, "messages": history}

@app.post("/api/memory/context")
async def get_project_context(req: MemoryQuery):
    context = project_memory.get_recent_context(req.session_id)
    return {"success": True, "session_id": req.session_id, "context": context}

@app.post("/api/memory/undo")
async def undo_last_change(req: MemoryQuery):
    undone = project_memory.undo_last_change(req.session_id)
    return {"success": bool(undone), "undone": undone}

# ── Evaluation Endpoints ─────────────────────────────────────────
@app.get("/api/evaluation/stats")
async def get_evaluation_stats(agent: Optional[str] = None):
    if agent:
        return {"success": True, "agent": agent, "stats": evaluation.get_agent_stats(agent)}
    return {"success": True, "stats": evaluation.get_summary()}

@app.get("/api/runs/{run_id}")
async def get_run_details(run_id: str):
    """Observability endpoint: return the full state+trace+metrics for a run."""
    run = evaluation.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return {"success": True, "run_id": run_id, "run": run}

@app.get("/api/runs")
async def list_runs(limit: int = 50):
    runs = evaluation.get_summary().get("total_runs", 0)
    return {"success": True, "total_runs": runs}

# ── Model & Provider Endpoints ───────────────────────────────────
@app.get("/api/models")
async def list_models_api(provider: Optional[str] = None):
    models = list_models(provider)
    status = keyring.status()
    out = []
    for m in models:
        meta = status.get(m["provider"], {})
        if m.get("custom"):
            key_configured = bool(m.get("api_key") or keyring.model_key_configured(m["id"]))
        else:
            key_configured = meta.get("configured", False)
        out.append({
            "id": m["id"],
            "name": m["name"],
            "provider": m["provider"],
            "provider_name": meta.get("name", "Custom") if not m.get("custom") else m.get("base_url", "Custom"),
            "key_configured": key_configured,
            "fast": m["fast"],
            "free": m.get("free", False),
            "custom": bool(m.get("custom")),
            "base_url": m.get("base_url", "") if m.get("custom") else "",
            "input_per_1m": m["input_per_1m"],
            "output_per_1m": m["output_per_1m"],
            "active": m["id"] == active_model,
        })
    return {"success": True, "models": out, "current": active_model}

@app.get("/api/models/current")
async def get_active_model():
    meta = get_model(active_model)
    return {"success": True, "model": active_model,
            "name": (meta or {}).get("name", active_model)}

@app.post("/api/models")
async def set_active_model(req: ModelRequest):
    global active_model
    meta = get_model(req.model)
    if not meta:
        raise HTTPException(status_code=400, detail=f"Unknown model: {req.model}")
    provider = meta.get("provider", "")
    if meta.get("custom"):
        has_key = bool(meta.get("api_key") or keyring.model_key_configured(req.model))
        if not has_key:
            raise HTTPException(
                status_code=409,
                detail=f"Model '{req.model}' has no API key. Add one in Settings first.",
            )
    else:
        status = keyring.status()
        if not status.get(provider, {}).get("configured", False):
            raise HTTPException(
                status_code=409,
                detail=f"Provider '{provider}' has no API key configured. Add one in Settings first.",
            )
    active_model = req.model
    _apply_active_model()
    audit_logger.log("model_changed", "engineer", "workflow", {"model": req.model})
    return {"success": True, "model": active_model}

@app.post("/api/models/custom")
async def add_custom_model(req: CustomModelRequest):
    try:
        meta = register_custom_model(req.model_id, req.name, req.api_key, req.base_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if req.api_key:
        keyring.set_model_key(meta["id"], req.api_key)
    _apply_active_model()
    audit_logger.log("custom_model_added", "engineer", "workflow",
                     {"model_id": meta["id"], "name": meta["name"]})
    return {"success": True, "model": {k: v for k, v in meta.items() if k != "api_key"},
            "masked_key": (req.api_key[:4] + "…" + req.api_key[-4:]) if len(req.api_key) > 8 else "…"}

@app.delete("/api/models/custom")
async def remove_custom_model(model_id: str = Query(...)):
    removed = unregister_custom_model(model_id)
    keyring.clear_model_key(model_id)
    if not removed:
        raise HTTPException(status_code=404, detail=f"Custom model not found: {model_id}")
    _apply_active_model()
    audit_logger.log("custom_model_removed", "engineer", "workflow", {"model_id": model_id})
    return {"success": True, "removed": model_id}

@app.get("/api/providers")
async def list_providers():
    return {"success": True, "providers": keyring.status()}

@app.get("/api/models/base-urls")
async def get_base_urls():
    return {"success": True, "base_urls": list_base_urls()}

@app.post("/api/providers/keys")
async def set_provider_key(req: ProviderKeyRequest):
    try:
        keyring.set_key(req.provider, req.key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    _apply_active_model()
    audit_logger.log("provider_key_updated", "engineer", "workflow",
                     {"provider": req.provider}, "success")
    return {"success": True, **keyring.status().get(req.provider, {})}

@app.post("/api/models/keys")
async def set_model_key(req: ModelKeyRequest):
    meta = get_model(req.model_id)
    if not meta:
        raise HTTPException(status_code=400, detail=f"Unknown model: {req.model_id}")
    if meta.get("custom"):
        keyring.set_model_key(req.model_id, req.api_key)
        meta["api_key"] = req.api_key.strip()
    else:
        keyring.set_key(meta["provider"], req.api_key)
    _apply_active_model()
    audit_logger.log("model_key_updated", "engineer", "workflow", {"model_id": req.model_id})
    return {"success": True, "model_id": req.model_id, "configured": True}

# ── Audit Endpoints ──────────────────────────────────────────────
@app.get("/api/audit/logs")
async def get_audit_logs(limit: int = 100, action: Optional[str] = None):
    return {"success": True, "logs": audit_logger.get_logs(limit, action)}

@app.get("/api/audit/stats")
async def get_audit_stats():
    return {"success": True, "stats": audit_logger.get_stats()}

# ── Tool Calling Endpoint ────────────────────────────────────────
@app.post("/api/tools/call")
async def call_tool(req: ToolCallRequest):
    result = await tool_registry.call(req.tool, **req.params)
    return {"success": result["success"], **result}

@app.get("/api/tools/list")
async def list_tools():
    return {"success": True, "tools": tool_registry.list_tools()}

# ── Maps status endpoint ─────────────────────────────────────────
@app.get("/api/maps/status")
async def maps_status():
    return {"success": True, "configured": maps_client.has_credentials()}

# ── WebSocket for real-time streaming ────────────────────────────
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    active_connections[client_id] = websocket
    logger.info("WebSocket connected", client_id=client_id)
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get("action") == "start_travel":
                intent = msg.get("intent", "")

                async def _on_step(step: str):
                    await websocket.send_json({"type": "step", "step": step})

                await websocket.send_json({"type": "status", "message": "Travel plan started", "step": "plan"})
                result = await travel_workflow.run(
                    intent,
                    origin=msg.get("origin"), destination=msg.get("destination"),
                    travel_modes=msg.get("travel_modes"), meal_types=msg.get("meal_types"),
                    time_budget_minutes=msg.get("time_budget_minutes"),
                    session_id=client_id, user_id=client_id,
                    on_step=_on_step,
                )
                await websocket.send_json({"type": "complete", "result": result})
            elif msg.get("action") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        active_connections.pop(client_id, None)
        logger.info("WebSocket disconnected", client_id=client_id)

# ── Background Workflow Runner ──────────────────────────────────
async def run_workflow(workflow_id: str, intent: str,
                       origin: Optional[str] = None, destination: Optional[str] = None,
                       travel_modes: Optional[List[str]] = None,
                       meal_types: Optional[List[str]] = None,
                       time_budget_minutes: Optional[int] = None,
                       preferences: Optional[Dict[str, Any]] = None,
                       session_id: str = "default", user_id: str = "engineer"):
    async def _on_step(step: str):
        entry = workflow_state.get(workflow_id) or {}
        entry["current_step"] = step
        entry["status"] = "running"
        workflow_state[workflow_id] = entry
        if session_id in active_connections:
            try:
                await active_connections[session_id].send_json({"type": "step", "step": step})
            except Exception:
                pass

    try:
        logger.info("Starting travel workflow", workflow_id=workflow_id, intent=intent)
        result = await travel_workflow.run(
            intent, origin=origin, destination=destination,
            travel_modes=travel_modes, meal_types=meal_types,
            time_budget_minutes=time_budget_minutes, preferences=preferences,
            session_id=session_id, user_id=user_id, run_id=workflow_id,
            on_step=_on_step,
        )

        if isinstance(result, dict):
            result.setdefault("workflow_id", workflow_id)
            result.setdefault("intent", intent)
        workflow_state[workflow_id] = result

        if session_id in active_connections:
            try:
                ws = active_connections[session_id]
                await ws.send_json({"type": "workflow_complete", "workflow_id": workflow_id, "result": result})
            except Exception:
                pass

        logger.info("Travel workflow completed", workflow_id=workflow_id,
                    success=result.get("current_step") == "complete")
    except Exception as e:
        logger.error("Travel workflow execution failed", workflow_id=workflow_id, error=str(e))
        workflow_state[workflow_id] = {"error": str(e), "success": False}

# ── Lifecycle ────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    logger.info("Multi-Agent Travelling Agent starting")
    problems = validate_settings()
    if problems:
        for problem in problems:
            logger.error("Startup validation failed", problem=problem)
        logger.error("Refusing to start: fix the configuration above (see backend/.env and .env.example).")
        raise RuntimeError("; ".join(problems))
    for warning in validate_optional():
        logger.warning("Startup warning", problem=warning)
    _apply_active_model()
    logger.info("Active model", model=active_model)
    logger.info("Google Maps client configured", configured=maps_client.has_credentials())

@app.on_event("shutdown")
async def shutdown():
    logger.info("Multi-Agent Travelling Agent shutting down")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)