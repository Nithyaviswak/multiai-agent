from typing import Dict, Any, List
import re
from app.logging_config import logger


class Guardrails:
    """Input/output guardrails for the travel agent.

    Two layers:
      1. ``validate_input``  - block destructive/system-wide/injection patterns.
      2. ``sanitize_output`` - redact secrets/credentials from any LLM output.

    All checks are deterministic regex based so behaviour is testable and
    auditable (no LLM in the trust boundary).
    """

    BLOCKED_PATTERNS = [
        r"rm\s+-rf\s*/",                     # recursive root wipe
        r"drop\s+table",                     # DB destruction
        r"shutdown\s+system",                # halt the whole system
        r"format\s+disk",                    # disk format
        r"del\s+/[fs]",                      # windows-ish delete
        r"password\s+(get|retrieve|recover|reveal|show)",  # credential theft
        r"(get|retrieve|recover|reveal|show)\s+.*(password|credential|secret)\s+(for|of|from)",  # credential theft
        r"send\s+(credentials?|password|api[_ ]?key|secrets?)\s+(to|via|over)",  # exfil
        r"grant\s+(all|admin|root)\s+(access|rights|privileges)\s+to",  # privilege dump
        r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",     # prompt injection
        r"forget\s+(all\s+)?(previous|prior|above)",                    # prompt injection
        r"system\s+(prompt|instructions?)\s*[:=]",                      # override attempt
    ]

    # Credentials/secret keys to redact from LLM output.
    SECRET_KEYS = r"(api[_ ]?key|password|secret|token|access[-_ ]?key|private[-_ ]?key)"
    KNOWN_ENV_VARS = (r"aws_access_key_id|aws_secret_access_key|GITHUB_TOKEN|"
                      r"GROQ_API_KEY|TAVILY_API_KEY|GOOGLE_MAPS_API_KEY")

    @staticmethod
    def validate_input(user_input: str) -> Dict[str, Any]:
        issues = []
        text = user_input or ""
        for pattern in Guardrails.BLOCKED_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                issues.append(f"Blocked pattern detected: {pattern}")
        return {"safe": len(issues) == 0, "issues": issues}

    @staticmethod
    def sanitize_output(text: str) -> str:
        if not text:
            return text
        redacted = re.sub(
            rf"({Guardrails.SECRET_KEYS})\s*[:=]\s*\S+",
            r"\1: [REDACTED]", text, flags=re.IGNORECASE)
        return re.sub(
            rf"({Guardrails.KNOWN_ENV_VARS})\s*[:=]\s*\S+",
            r"\1: [REDACTED]", redacted, flags=re.IGNORECASE)


guardrails = Guardrails()