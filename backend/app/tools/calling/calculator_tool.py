from typing import Dict, Any
import math

class CalculatorTool:
    description = "Perform mathematical calculations"

    async def execute(self, expression: str) -> Dict[str, Any]:
        allowed = set("0123456789+-*/.()% ")
        if not all(c in allowed for c in expression):
            return {"error": "Invalid characters in expression"}
        try:
            result = eval(expression, {"__builtins__": {}}, {"math": math})
            return {"expression": expression, "result": result}
        except Exception as e:
            return {"error": str(e), "expression": expression}


calculator_tool = CalculatorTool()
