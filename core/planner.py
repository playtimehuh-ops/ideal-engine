"""
Planner - turns an AI reply into either a spoken answer or a tool action.

Why not OpenRouter's native "tools" parameter? Because many free-tier models
don't support function calling reliably, and this app defaults to a free
model. Instead we use a plain-text convention that works with almost any
chat model: "if you want to act, reply with ONLY a JSON object like
{"tool": "...", "args": {...}}". This is parsed here, executed with the
safety/confirmation gate, and the result is fed back for a natural reply.
"""

import json
import re

from tools.registry import TOOL_MAP, describe_tools_for_prompt
from core.safety import CONFIRMATION_REQUIRED_TOOLS

_JSON_FENCE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)

PERSONA = (
    "You are Alex, a calm, intelligent, and friendly personal desktop assistant "
    "running locally on the user's own Windows computer. Speak naturally and "
    "concisely, like a sharp, likeable friend - never robotic, never movie-butler "
    "dialogue. Never say things like 'Certainly, sir' or 'At your service' or "
    "'As you wish'. Keep answers reasonably short unless the user is asking for "
    "detail."
)

ACTION_INSTRUCTIONS = (
    "You have a small set of tools you can use to act on the user's computer or "
    "search the web. To use exactly one tool, reply with ONLY a single JSON "
    "object and nothing else - no other words, no markdown fences:\n"
    '{{"tool": "<tool_name>", "args": {{...}}}}\n\n'
    "Available tools:\n{tool_list}\n\n"
    "If no tool is needed, just reply normally in plain conversational text - "
    "never wrap a normal reply in JSON, and never invent a tool name that "
    "isn't listed above."
)


def build_system_prompt(memory_block: str) -> str:
    return (
        f"{PERSONA}\n\n"
        f"{ACTION_INSTRUCTIONS.format(tool_list=describe_tools_for_prompt())}\n\n"
        f"Known facts the user has told you to remember:\n{memory_block}"
    )


def _strip_fence(text: str) -> str:
    m = _JSON_FENCE.match(text.strip())
    return m.group(1) if m else text.strip()


def parse_action(ai_text: str):
    """
    Returns (tool_name, args) if ai_text is a valid tool-call JSON matching a
    known tool, otherwise (None, None) meaning "treat as plain text reply".
    """
    candidate = _strip_fence(ai_text)
    if not (candidate.startswith("{") and candidate.endswith("}")):
        return None, None
    try:
        obj = json.loads(candidate)
    except json.JSONDecodeError:
        return None, None

    tool_name = obj.get("tool")
    args = obj.get("args", {}) or {}
    if tool_name not in TOOL_MAP or not isinstance(args, dict):
        return None, None
    return tool_name, args


def run_tool(tool_name: str, args: dict, confirmation_gate, stop_controller, db) -> str:
    """
    Executes a tool with the confirmation gate enforced here - the AI has no
    path to skip this. Returns a plain-text result to feed back to the model.
    """
    if stop_controller.is_stopped():
        return "Action cancelled by the user."

    tool = TOOL_MAP[tool_name]

    if tool_name in CONFIRMATION_REQUIRED_TOOLS or tool.get("confirm"):
        allowed = confirmation_gate.ask(tool_name, args)
        if not allowed:
            db.log_activity("tool_denied", f"{tool_name} {args}")
            return "The user declined to confirm this action, so it was not performed."

    if stop_controller.is_stopped():
        return "Action cancelled by the user."

    try:
        result = tool["func"](args)
    except Exception as e:
        result = f"The tool failed unexpectedly: {e}"

    db.log_activity("tool_run", f"{tool_name} {args} -> {result}")
    return result
