import asyncio, json, sys
sys.path.insert(0, '.')
from app.graph.workflow import NetworkWorkflow
from langgraph.graph import StateGraph, END

async def test():
    wf = NetworkWorkflow()
    # Add recursion limit
    initial = {
        "intent": "Configure OSPF on core-router-01",
        "intent_complete": False, "intent_data": None,
        "knowledge_data": None,
        "topology_complete": False, "topology_data": None,
        "netconf_complete": False, "netconf_data": None,
        "config_complete": False, "config_data": None,
        "automation_data": None,
        "verification_complete": False, "verification_data": None,
        "monitoring_data": None,
        "compliance_complete": False, "compliance_data": None,
        "log_analysis_complete": False, "log_analysis_data": None,
        "incident_response_data": None,
        "summary_data": None, "summary_complete": False,
        "session_id": "test", "user_id": "engineer",
        "requires_approval": False, "approved": False,
        "approval_id": None, "errors": [],
        "current_step": "plan", "retry_count": 0, "should_retry": False,
    }
    try:
        result = await wf.graph.ainvoke(initial, {"recursion_limit": 100})
        print("SUCCESS:", json.dumps({"current_step": result.get("current_step"), "has_intent": result.get("intent_data") is not None}, indent=2))
    except Exception as e:
        print(f"ERROR: {e}")

asyncio.run(test())
