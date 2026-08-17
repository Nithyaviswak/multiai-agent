from typing import Dict, Any, List
from app.agents.base import BaseAgent
from app.logging_config import logger

class MonitoringAgent(BaseAgent):
    """Monitoring Agent that simulates real-time network metrics"""

    SIMULATED_METRICS = {
        "core-router-01": {"cpu": 45.2, "memory": 68.1, "latency_ms": 1.2, "packet_loss": 0.0, "uptime_days": 120},
        "edge-router-01": {"cpu": 72.8, "memory": 81.5, "latency_ms": 4.7, "packet_loss": 0.3, "uptime_days": 45},
        "distribution-sw-01": {"cpu": 33.1, "memory": 55.3, "latency_ms": 0.8, "packet_loss": 0.0, "uptime_days": 200},
        "access-sw-01": {"cpu": 22.4, "memory": 44.2, "latency_ms": 0.5, "packet_loss": 0.0, "uptime_days": 365},
    }

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Monitoring agent started")

        try:
            from app.tools.network.device_simulator import device_simulator
            devices = device_simulator.get_all_devices()

            metrics = {}
            alerts = []
            for device in devices:
                hostname = device["hostname"]
                base = self.SIMULATED_METRICS.get(hostname, {"cpu": 50, "memory": 50, "latency_ms": 1, "packet_loss": 0, "uptime_days": 100})
                metrics[hostname] = base

                if base["cpu"] > 70:
                    alerts.append({"device": hostname, "metric": "cpu", "value": base["cpu"], "severity": "warning", "message": f"CPU high on {hostname}: {base['cpu']}%"})
                if base["memory"] > 80:
                    alerts.append({"device": hostname, "metric": "memory", "value": base["memory"], "severity": "warning", "message": f"Memory high on {hostname}: {base['memory']}%"})
                if base["packet_loss"] > 0:
                    alerts.append({"device": hostname, "metric": "packet_loss", "value": base["packet_loss"], "severity": "critical", "message": f"Packet loss on {hostname}: {base['packet_loss']}%"})

            interface_status = {}
            for device in devices:
                for iface_name, iface_data in device["interfaces"].items():
                    interface_status[f"{device['hostname']}_{iface_name}"] = iface_data["status"]

            monitoring_data = {
                "metrics": metrics,
                "alerts": alerts,
                "interface_status": interface_status,
                "total_devices": len(devices),
                "active_alerts": len(alerts),
                "overall_health": self._calc_health(metrics),
            }

            return {
                "monitoring_data": monitoring_data,
                "monitoring_complete": True,
                "current_step": "monitoring",
            }

        except Exception as e:
            logger.error("Monitoring agent failed", error=str(e))
            return {
                "monitoring_data": None,
                "monitoring_complete": False,
                "errors": state.get("errors", []) + [f"Monitoring failed: {str(e)}"],
            }

    def _calc_health(self, metrics: Dict) -> str:
        scores = []
        for m in metrics.values():
            cpu_score = max(0, 100 - m["cpu"])
            mem_score = max(0, 100 - m["memory"])
            loss_score = 100 if m["packet_loss"] == 0 else max(0, 100 - m["packet_loss"] * 10)
            scores.append((cpu_score + mem_score + loss_score) / 3)
        avg = sum(scores) / len(scores) if scores else 0
        if avg >= 80: return "healthy"
        elif avg >= 50: return "degraded"
        return "critical"
