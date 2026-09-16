from app.tools.calling.registry import tool_registry
from app.tools.calling.search_tool import search_tool
from app.tools.calling.calculator_tool import calculator_tool
from app.tools.calling.python_executor import python_executor
from app.tools.calling.report_generator_tool import report_generator_tool

tool_registry.register("search", search_tool)
tool_registry.register("calculator", calculator_tool)
tool_registry.register("python", python_executor)
tool_registry.register("report_generator", report_generator_tool)

__all__ = ["tool_registry"]