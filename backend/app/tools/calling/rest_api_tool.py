from typing import Dict, Any
import json

class RESTAPITool:
    description = "Make REST API calls to external systems"

    async def execute(self, method: str, endpoint: str, body: Dict = None) -> Dict[str, Any]:
        simulated_responses = {
            "get_devices": {"devices": ["core-router-01", "edge-router-01"]},
            "get_interfaces": {"interfaces": {"Gig0/0": "up", "Gig0/1": "up"}},
            "get_config": {"running_config": "hostname router\n!"},
        }
        key = f"{method.lower()}_{endpoint.split('/')[-1]}"
        result = simulated_responses.get(key, {"message": f"Simulated {method} {endpoint}", "body": body})
        return {"success": True, "status_code": 200, "data": result}


rest_api_tool = RESTAPITool()
