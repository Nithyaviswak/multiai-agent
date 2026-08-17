from typing import Dict, Any, List
from datetime import datetime, timezone
from app.logging_config import logger

class AuditLogger:
    """Audit logging for all system actions"""

    def __init__(self):
        self._logs: List[Dict[str, Any]] = []

    def log(self, action: str, user: str, resource: str, details: Dict[str, Any],
            status: str = "success"):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "user": user,
            "resource": resource,
            "details": details,
            "status": status,
        }
        self._logs.append(entry)
        logger.info("Audit", **entry)
        return entry

    def get_logs(self, limit: int = 100, action: str = None) -> List[Dict[str, Any]]:
        logs = self._logs
        if action:
            logs = [l for l in logs if l["action"] == action]
        return logs[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        total = len(self._logs)
        actions = {}
        for log in self._logs:
            actions[log["action"]] = actions.get(log["action"], 0) + 1
        return {"total_actions": total, "action_breakdown": actions}


audit_logger = AuditLogger()
