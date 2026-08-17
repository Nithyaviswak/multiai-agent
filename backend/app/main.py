from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import asyncio
import json
from app.graph.workflow import network_workflow
from app.logging_config import logger
from app.config import settings, validate_settings
from app.tools.rate_limiter import rate_limiter
from app.tools.network.device_simulator import device_simulator
from app.tools.memory import conversation_memory, project_memory
from app.tools.audit import audit_logger
from app.tools.evaluation import evaluation
from app.tools.rbac import rbac
from app.tools.guardrails import guardrails
from app.tools.calling.registry import tool_registry
from app.tools.model_registry import list_models, get_model, PROVIDERS
from app.tools.keyring import keyring

app = FastAPI(
    title="Multi-Agent AI Network Automation Platform",
    description="Enterprise multi-agent platform with planner, knowledge, config, compliance, monitoring, automation, and report agents. Features hybrid RAG, tool calling, memory, human-in-the-loop approval, RBAC, audit logging, and evaluation pipelines.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request/Response Models ─────────────────────────────────────
class NetworkRequest(BaseModel):
    intent: str
    environment: Optional[str] = "devnet-sandbox"
    session_id: Optional[str] = "default"
    user_id: Optional[str] = "engineer"

class NetworkResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]]
    error: Optional[str]
    workflow_id: Optional[str]

class ApprovalRequest(BaseModel):
    workflow_id: str
    approved: bool
    user_id: str

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
    network_workflow.set_model(active_model)

# ── WebSocket Connections ────────────────────────────────────────
active_connections: Dict[str, WebSocket] = {}

# ── Root ─────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "message": "Multi-Agent AI Network Automation Platform",
        "version": "2.0.0",
        "environments": list(device_simulator.get_environments().keys()),
        "devices": [d["hostname"] for d in device_simulator.get_all_devices()],
        "agents": ["Planner", "Knowledge", "Topology", "NETCONF", "Configuration",
                    "Automation", "Verification", "Monitoring", "Compliance",
                    "LogAnalyzer", "IncidentResponse", "ReportGenerator"],
        "tools": [t["name"] for t in tool_registry.list_tools()],
        "features": ["tool_calling", "memory", "human_approval", "rbac",
                      "audit_logging", "evaluation", "guardrails", "websockets"],
    }

# ── Workflow Endpoints ───────────────────────────────────────────
@app.post("/api/network", response_model=NetworkResponse)
async def start_network_workflow(request: NetworkRequest, background_tasks: BackgroundTasks):
    try:
        if not await rate_limiter.check_limit(request.user_id):
            raise HTTPException(status_code=429, detail="Rate limit exceeded, try again later")

        if not request.intent.strip():
            raise HTTPException(status_code=400, detail="Network intent is required")

        guard_check = guardrails.validate_input(request.intent)
        if not guard_check["safe"]:
            raise HTTPException(status_code=400, detail=f"Input blocked: {guard_check['issues']}")

        import uuid
        workflow_id = str(uuid.uuid4())

        workflow_state[workflow_id] = {
            "workflow_id": workflow_id,
            "intent": request.intent,
            "environment": request.environment,
            "session_id": request.session_id,
            "user_id": request.user_id,
            "current_step": "plan",
            "status": "running",
        }

        background_tasks.add_task(
            run_workflow, workflow_id, request.intent, request.environment,
            request.session_id, request.user_id
        )

        audit_logger.log("workflow_started", request.user_id, "workflow",
                         {"intent": request.intent, "id": workflow_id})
        _prune_workflow_state()

        return NetworkResponse(
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

@app.get("/api/network/{workflow_id}")
async def get_workflow_result(workflow_id: str):
    if workflow_id not in workflow_state:
        raise HTTPException(status_code=404, detail="Workflow not found")
    result = workflow_state[workflow_id]
    if "error" in result:
        return NetworkResponse(success=False, data=None, error=result["error"], workflow_id=workflow_id)
    return NetworkResponse(success=True, data=result, error=None, workflow_id=workflow_id)

# ── Approval Endpoint ────────────────────────────────────────────
@app.post("/api/approve")
async def approve_action(req: ApprovalRequest):
    if req.workflow_id not in workflow_state:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if not rbac.check_permission(req.user_id, "configure"):
        raise HTTPException(status_code=403, detail="User lacks permission to approve")

    saved = workflow_state[req.workflow_id]
    if saved.get("current_step") != "awaiting_approval":
        raise HTTPException(status_code=400, detail="Workflow is not awaiting approval")

    result = await network_workflow.resume_after_approval(saved, req.approved)
    workflow_state[req.workflow_id] = result

    audit_logger.log("approval", req.user_id, "workflow",
                     {"workflow_id": req.workflow_id, "approved": req.approved},
                     "approved" if req.approved else "denied")

    return {"success": True, "approved": req.approved,
            "status": result.get("terminal_status")}

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
    undone = project_memory.undo_last_config(req.session_id)
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
        out.append({
            "id": m["id"],
            "name": m["name"],
            "provider": m["provider"],
            "provider_name": meta.get("name", m["provider"]),
            "key_configured": meta.get("configured", False),
            "fast": m["fast"],
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

@app.get("/api/providers")
async def list_providers():
    return {"success": True, "providers": keyring.status()}

@app.post("/api/providers/keys")
async def set_provider_key(req: ProviderKeyRequest):
    try:
        keyring.set_key(req.provider, req.key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    # Rebuild clients with the new key for the active model's provider.
    _apply_active_model()
    audit_logger.log("provider_key_updated", "engineer", "workflow",
                     {"provider": req.provider}, "success")
    return {"success": True, **keyring.status().get(req.provider, {})}

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

# ── Device / Topology Endpoints ──────────────────────────────────
@app.get("/api/devices")
async def list_devices():
    return {"success": True, "devices": device_simulator.get_all_devices(), "environments": device_simulator.get_environments()}

@app.get("/api/topology")
async def get_topology():
    return {"success": True, "topology": device_simulator.get_topology()}

@app.get("/api/environments")
async def get_environments():
    return {"success": True, "environments": device_simulator.get_environments()}

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
            if msg.get("action") == "start_workflow":
                intent = msg.get("intent", "")
                environment = msg.get("environment", "devnet-sandbox")
                await websocket.send_json({"type": "status", "message": "Workflow started", "step": "plan"})
                result = await network_workflow.run(intent, environment, client_id, client_id)
                await websocket.send_json({"type": "complete", "result": result})
            elif msg.get("action") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        active_connections.pop(client_id, None)
        logger.info("WebSocket disconnected", client_id=client_id)

# ── Background Workflow Runner ──────────────────────────────────
async def run_workflow(workflow_id: str, intent: str, environment: str,
                       session_id: str = "default", user_id: str = "engineer"):
    try:
        logger.info("Starting workflow", workflow_id=workflow_id, intent=intent)
        result = await network_workflow.run(intent, environment, session_id, user_id,
                                            run_id=workflow_id)

        if isinstance(result, dict):
            result.setdefault("workflow_id", workflow_id)
            result.setdefault("intent", intent)
        workflow_state[workflow_id] = result

        # Notify WebSocket if connected
        if session_id in active_connections:
            try:
                ws = active_connections[session_id]
                await ws.send_json({"type": "workflow_complete", "workflow_id": workflow_id, "result": result})
            except Exception:
                pass

        logger.info("Workflow completed", workflow_id=workflow_id, success=result.get("current_step") == "complete")
    except Exception as e:
        logger.error("Workflow execution failed", workflow_id=workflow_id, error=str(e))
        workflow_state[workflow_id] = {"error": str(e), "success": False}

# ── Lifecycle ────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    logger.info("Network Automation Platform v2.0.0 starting")
    problems = validate_settings()
    if problems:
        for problem in problems:
            logger.error("Startup validation failed", problem=problem)
        logger.error("Refusing to start: fix the configuration above (see backend/.env and .env.example).")
        raise RuntimeError("; ".join(problems))
    for env_name, env_data in device_simulator.get_environments().items():
        logger.info("Environment available", name=env_data["name"], type=env_data["type"])
    _apply_active_model()
    logger.info("Active model", model=active_model)

@app.on_event("shutdown")
async def shutdown():
    logger.info("Network Automation Platform shutting down")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)
