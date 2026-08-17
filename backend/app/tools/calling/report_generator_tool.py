from typing import Dict, Any, List
from datetime import datetime, timezone

class ReportGeneratorTool:
    description = "Generate structured executive reports"

    async def execute(self, title: str, sections: Dict[str, str],
                      metrics: Dict[str, Any] = None) -> Dict[str, Any]:
        metrics = metrics or {}
        report = {
            "title": title,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "sections": sections,
            "metrics": metrics,
            "word_count": sum(len(v.split()) for v in sections.values()),
        }
        return report


report_generator_tool = ReportGeneratorTool()
