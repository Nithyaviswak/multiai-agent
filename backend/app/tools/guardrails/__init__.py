from typing import Dict, Any, List, Optional
import re
from app.logging_config import logger


class Guardrails:
    """Input/output guardrails for safety and validation.

    Three layers:
      1. ``validate_input``  - block destructive/system-wide patterns in user intent.
      2. ``validate_config`` - allow-list of Cisco-style config commands; reject
         unknown or destructive directives.
      3. ``sanitize_output`` - redact secrets/credentials from any LLM output.

    All checks are deterministic regex/allow-list based so behaviour is testable
    and auditable (no LLM in the trust boundary).
    """

    BLOCKED_PATTERNS = [
        r"rm\s+-rf\s*/",                     # recursive root wipe
        r"drop\s+table",                     # DB destruction
        r"shutdown\s+system",                # halt the whole system
        r"format\s+disk",                    # disk format
        r"del\s+/[fs]",                      # windows-ish delete
        r"reload\s+all",                     # reload every device
        r"erase\s+flash",                    # wipe flash on devices
        r"erase\s+startup",                  # wipe startup-config
        r"default\s+interface\s+all",        # reset all interfaces
        r"disable\s+.*(firewall|security)",  # turn off all security
        r"password\s+(get|retrieve|recover|reveal|show)",  # credential theft
        r"(get|retrieve|recover|reveal|show)\s+.*(password|credential|secret)\s+(for|of|from)",  # credential theft
        r"send\s+(credentials?|password|api[_ ]?key|secrets?)\s+(to|via|over)",  # exfil
        r"grant\s+(all|admin|root)\s+(access|rights|privileges)\s+to",  # privilege dump
        r"delete\s+.*(config|database|backup)\s+(.*)\s+and\s+(.*)\s+everything",
    ]

    # Commands that mutate state and therefore should never appear in analysis-only
    # contexts; kept as a secondary net under ALLOWED_CONFIG_CMDS.
    DESTRUCTIVE_CONFIG_CMDS = {
        "erase", "delete flash", "delete nvram", "format", "reload",
        "poweroff", "shutdown all",
    }

    ALLOWED_CONFIG_CMDS = {
        "router", "bgp", "router-id", "network", "neighbor", "address-family",
        "activate", "update-source", "passive-interface", "default-information",
        "redistribute", "area", "interface", "vlan", "name", "ip", "ipv6",
        "switchport", "hostname", "username", "enable", "service", "logging",
        "ntp", "snmp", "access-list", "deny", "permit", "access-group",
        "route-map", "prefix-list", "community-list", "banner", "line",
        "crypto", "redundancy", "clock", "no", "shutdown", "description",
        "speed", "duplex", "bandwidth", "mtu", "spanning-tree",
    }

    # Known-good device hostnames to cross-check targets against (from simulator).
    KNOWN_DEVICES = {
        "core-router-01", "core-router-02", "edge-router-01", "edge-router-02",
        "access-switch-01", "access-switch-02", "firewall-01", "firewall-02",
        "core-switch-01", "core-switch-02",
    }

    # Credentials/secret keys to redact from LLM output.
    SECRET_KEYS = r"(api[_ ]?key|password|secret|token|access[-_ ]?key|private[-_ ]?key)"

    @staticmethod
    def validate_input(user_input: str) -> Dict[str, Any]:
        issues = []
        text = user_input or ""
        for pattern in Guardrails.BLOCKED_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                issues.append(f"Blocked pattern detected: {pattern}")
        return {"safe": len(issues) == 0, "issues": issues}

    @staticmethod
    def validate_config(config_lines: List[str]) -> Dict[str, Any]:
        issues = []
        blocked = []
        allowed = Guardrails.ALLOWED_CONFIG_CMDS
        for line in config_lines or []:
            stripped = (line or "").strip()
            if not stripped:
                continue
            lower = stripped.lower()
            if lower.startswith("!") or lower.startswith("#"):
                continue
            if any(lower.startswith(d) for d in Guardrails.DESTRUCTIVE_CONFIG_CMDS):
                blocked.append(stripped)
                continue
            if not any(lower.startswith(cmd) for cmd in allowed):
                issues.append(f"Unknown command: {stripped}")
        return {
            "safe": len(issues) == 0 and len(blocked) == 0,
            "issues": issues,
            "blocked_commands": blocked,
            "total_lines": len(config_lines or []),
        }

    @staticmethod
    def validate_target_devices(devices: List[str]) -> Dict[str, Any]:
        """Warn about targets not in the known inventory (may be hallucinated)."""
        unknown = [d for d in (devices or []) if d not in Guardrails.KNOWN_DEVICES]
        return {
            "safe": len(unknown) == 0,
            "unknown_devices": unknown,
        }

    @staticmethod
    def sanitize_output(text: str) -> str:
        if not text:
            return text
        redacted = re.sub(
            rf"({Guardrails.SECRET_KEYS})\s*[:=]\s*\S+",
            r"\1: [REDACTED]", text, flags=re.IGNORECASE)
        return re.sub(
            r"(aws_access_key_id|aws_secret_access_key|GITHUB_TOKEN|GROQ_API_KEY|TAVILY_API_KEY)\s*[:=]\s*\S+",
            r"\1: [REDACTED]", redacted, flags=re.IGNORECASE)


guardrails = Guardrails()