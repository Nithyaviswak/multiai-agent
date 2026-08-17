from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from app.logging_config import logger

class ConversationMemory:
    """Stores conversation history per session"""
    def __init__(self):
        self._store: Dict[str, List[Dict[str, Any]]] = {}

    def add_message(self, session_id: str, role: str, content: str, metadata: Optional[Dict] = None):
        if session_id not in self._store:
            self._store[session_id] = []
        self._store[session_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {},
        })

    def get_history(self, session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        return self._store.get(session_id, [])[-limit:]

    def clear(self, session_id: str):
        self._store.pop(session_id, None)


class ProjectMemory:
    """Stores project-level state, configs, and preferences"""
    def __init__(self):
        self._projects: Dict[str, Dict[str, Any]] = {}
        self._user_prefs: Dict[str, Dict[str, Any]] = {}

    def create_project(self, project_id: str, name: str, owner: str):
        self._projects[project_id] = {
            "id": project_id,
            "name": name,
            "owner": owner,
            "created": datetime.now(timezone.utc).isoformat(),
            "configs": [],
            "devices": [],
            "state": "active",
        }

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        return self._projects.get(project_id)

    def add_config(self, project_id: str, config: Dict[str, Any]):
        proj = self._projects.get(project_id)
        if proj:
            proj["configs"].append({**config, "timestamp": datetime.now(timezone.utc).isoformat()})

    def set_user_preference(self, user_id: str, key: str, value: Any):
        if user_id not in self._user_prefs:
            self._user_prefs[user_id] = {}
        self._user_prefs[user_id][key] = value

    def get_user_preference(self, user_id: str, key: str, default: Any = None) -> Any:
        return self._user_prefs.get(user_id, {}).get(key, default)

    def get_recent_context(self, session_id: str, limit: int = 5) -> str:
        if session_id not in self._projects:
            return ""
        proj = self._projects[session_id]
        lines = [f"Project: {proj['name']}", f"State: {proj['state']}", f"Configs applied: {len(proj['configs'])}"]
        for cfg in proj["configs"][-limit:]:
            lines.append(f"  - {cfg.get('technology', 'unknown')} on {cfg.get('device', 'unknown')} at {cfg.get('timestamp', '')}")
        return "\n".join(lines)

    def undo_last_config(self, project_id: str) -> Optional[Dict[str, Any]]:
        proj = self._projects.get(project_id)
        if proj and proj["configs"]:
            return proj["configs"].pop()
        return None


conversation_memory = ConversationMemory()
project_memory = ProjectMemory()
