from typing import Dict, Any, List
from app.agents.base import BaseAgent
from app.tools.calling.python_executor import python_executor
from app.tools.guardrails import guardrails
from app.logging_config import logger

class AutomationAgent(BaseAgent):
    """Automation Agent that executes Python scripts and system commands"""

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        config_data = state.get("config_data", {})
        logger.info("Automation agent started")

        try:
            automation_results = []

            # Execute config application as automation
            configs = config_data.get("configurations", [])
            for cfg in configs:
                hostname = cfg["hostname"]
                config_lines = cfg.get("config_lines", [])

                # Validate with guardrails
                validation = guardrails.validate_config(config_lines)
                if not validation["safe"]:
                    automation_results.append({
                        "device": hostname,
                        "action": "validate",
                        "status": "blocked",
                        "issues": validation["issues"],
                    })
                    continue

                # Simulate automation execution
                from app.tools.network.netmiko_mock import netmiko_mock
                await netmiko_mock.connect(hostname)
                result = await netmiko_mock.send_config_set(hostname, config_lines)
                await netmiko_mock.save_config(hostname)
                await netmiko_mock.disconnect(hostname)

                automation_results.append({
                    "device": hostname,
                    "action": "apply_config",
                    "status": "success",
                    "result": result,
                })

            # Execute any automation scripts if present
            python_script = config_data.get("automation_script")
            if python_script:
                script_result = await python_executor.execute(python_script)
                automation_results.append({
                    "device": "automation_engine",
                    "action": "python_execution",
                    "status": "success" if "output" in script_result else "error",
                    "result": script_result.get("output", script_result.get("error", "")),
                })

            return {
                "automation_data": {
                    "results": automation_results,
                    "total_actions": len(automation_results),
                    "all_successful": all(r["status"] == "success" for r in automation_results),
                },
                "automation_complete": True,
                "current_step": "automation",
            }

        except Exception as e:
            logger.error("Automation agent failed", error=str(e))
            return {
                "automation_data": None,
                "automation_complete": False,
                "errors": state.get("errors", []) + [f"Automation failed: {str(e)}"],
            }
