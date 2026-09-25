"""
Aggregates every tool module into one lookup the planner uses.
Adding a new tool later = write a module exposing TOOLS = [...] and add it
to _TOOL_MODULES below. Nothing else needs to change.
"""

from tools import app_launcher, screenshot, mouse, keyboard, web_search

_TOOL_MODULES = [app_launcher, screenshot, mouse, keyboard, web_search]

ALL_TOOLS = []
for _module in _TOOL_MODULES:
    ALL_TOOLS.extend(_module.TOOLS)

TOOL_MAP = {t["name"]: t for t in ALL_TOOLS}


def describe_tools_for_prompt() -> str:
    """Human-readable tool list injected into the system prompt."""
    lines = []
    for t in ALL_TOOLS:
        params = t["parameters"]
        if params:
            param_str = ", ".join(f"{k} ({v})" for k, v in params.items())
        else:
            param_str = "no parameters"
        lines.append(f'- "{t["name"]}": {t["description"]} Parameters: {param_str}.')
    return "\n".join(lines)
