from typing import Dict, Any, List
import asyncio
import sys
from io import StringIO

class PythonExecutor:
    description = "Execute Python code in a sandboxed environment"

    async def execute(self, code: str, timeout: int = 5) -> Dict[str, Any]:
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            exec_globals = {"__builtins__": __builtins__}
            exec(code, exec_globals)
            output = sys.stdout.getvalue()
            return {"output": output, "execution_time_ms": 0}
        except Exception as e:
            return {"error": str(e), "output": ""}
        finally:
            sys.stdout = old_stdout


python_executor = PythonExecutor()
