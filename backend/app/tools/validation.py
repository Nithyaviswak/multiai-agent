from typing import Type, Any, Dict
from pydantic import BaseModel, ValidationError
from app.logging_config import logger

class ValidationTool:
    """Tool for validating agent outputs against Pydantic schemas"""
    
    @staticmethod
    async def validate_output(data: Dict[str, Any], schema: Type[BaseModel]) -> tuple[bool, Any, str]:
        """
        Validate data against Pydantic schema with error handling
        Returns: (is_valid, validated_data, error_message)
        """
        try:
            validated_data = schema(**data)
            return True, validated_data, ""
        except ValidationError as e:
            error_msg = f"Validation failed: {str(e)}"
            logger.warning("Output validation failed", errors=e.errors())
            return False, None, error_msg
    
    @staticmethod
    async def extract_json_from_text(text: str) -> Dict[str, Any]:
        """Extract JSON from LLM text response"""
        import re
        import json

        if not isinstance(text, str):
            return {"content": str(text)}

        text = text.strip()
        if not text:
            return {"content": ""}

        # 1) Whole response is JSON
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        # 2) JSON inside fenced code blocks
        fenced_blocks = re.findall(r"```(?:json)?\s*([\s\S]*?)```", text, flags=re.IGNORECASE)
        for block in fenced_blocks:
            candidate = block.strip()
            if not candidate:
                continue
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                continue

        # 3) Any balanced {...} object in free text
        in_string = False
        escaped = False
        depth = 0
        start_idx = -1

        for idx, char in enumerate(text):
            if char == "\\" and in_string:
                escaped = not escaped
                continue

            if char == '"' and not escaped:
                in_string = not in_string
            escaped = False

            if in_string:
                continue

            if char == "{":
                if depth == 0:
                    start_idx = idx
                depth += 1
            elif char == "}":
                if depth > 0:
                    depth -= 1
                    if depth == 0 and start_idx >= 0:
                        candidate = text[start_idx : idx + 1]
                        try:
                            parsed = json.loads(candidate)
                            if isinstance(parsed, dict):
                                return parsed
                        except json.JSONDecodeError:
                            start_idx = -1
                            continue

        logger.warning("Failed to extract JSON from text")
        return {"content": text}

validation_tool = ValidationTool()
