from typing import Dict, Any
from app.agents.configuration_agent import TEMPLATES


class ConfigGeneratorTool:
    description = "Generate network device configurations from shared templates"

    async def execute(self, technology: str, device: str, params: Dict = None) -> Dict[str, Any]:
        params = params or {}
        tech = technology.upper()
        if tech not in TEMPLATES or device not in TEMPLATES[tech]:
            return {"error": f"No template for {tech} on {device}"}
        config = list(TEMPLATES[tech][device])
        resolved = []
        for line in config:
            for k, v in params.items():
                line = line.replace(f"{{{k}}}", str(v))
            resolved.append(line)
        return {
            "device": device,
            "technology": tech,
            "config": "\n".join(resolved),
            "lines": resolved,
        }


config_generator_tool = ConfigGeneratorTool()