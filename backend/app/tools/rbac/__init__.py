from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import json
from app.logging_config import logger

ROLES = {"admin", "engineer", "viewer"}
ACTIONS = {"configure", "push", "delete", "backup", "audit"}

class RBACManager:
    """Simple role-based access control"""

    def __init__(self):
        self._users: Dict[str, Dict[str, Any]] = {
            "admin": {"role": "admin", "name": "Admin User"},
            "engineer": {"role": "engineer", "name": "Network Engineer"},
            "viewer": {"role": "viewer", "name": "Read-Only User"},
        }

    def check_permission(self, user_id: str, action: str) -> bool:
        user = self._users.get(user_id, {})
        role = user.get("role", "viewer")
        if role == "admin":
            return True
        if role == "engineer" and action not in {"delete"}:
            return True
        if role == "viewer" and action in {"audit"}:
            return True
        return False

    def requires_approval(self, action: str) -> bool:
        return action in {"configure", "push", "delete"}

    def get_user_role(self, user_id: str) -> str:
        return self._users.get(user_id, {}).get("role", "viewer")


rbac = RBACManager()
