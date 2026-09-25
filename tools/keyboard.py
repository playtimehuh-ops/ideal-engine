"""
type_text and press_key tools. Both confirmed before running - they inject
real keystrokes into whatever window currently has focus.
"""

# A safe allow-list of key names pyautogui understands, so the AI can't pass
# through something unexpected. This covers normal usage; extend if needed.
ALLOWED_KEYS = {
    "enter", "return", "tab", "space", "backspace", "delete", "esc", "escape",
    "up", "down", "left", "right", "home", "end", "pageup", "pagedown",
    "ctrl", "alt", "shift", "win",
    "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12",
    "ctrl+c", "ctrl+v", "ctrl+x", "ctrl+z", "ctrl+a", "ctrl+s",
}


def execute_type_text(args: dict) -> str:
    try:
        import pyautogui
    except Exception as e:
        return f"Typing isn't available: {e}"

    text = args.get("text")
    if not text:
        return "I didn't get any text to type."

    try:
        pyautogui.write(str(text), interval=0.02)
    except Exception as e:
        return f"I couldn't type that: {e}"

    return "Typed it."


def execute_press_key(args: dict) -> str:
    try:
        import pyautogui
    except Exception as e:
        return f"Key presses aren't available: {e}"

    key = (args.get("key") or "").strip().lower()
    if key not in ALLOWED_KEYS:
        return f"'{key}' isn't a key combination I'm allowed to press."

    try:
        if "+" in key:
            pyautogui.hotkey(*key.split("+"))
        else:
            pyautogui.press(key)
    except Exception as e:
        return f"I couldn't press that key: {e}"

    return f"Pressed {key}."


TOOLS = [
    {
        "name": "type_text",
        "description": "Type text into whatever window currently has focus.",
        "parameters": {"text": "string - the text to type"},
        "confirm": True,
        "func": execute_type_text,
    },
    {
        "name": "press_key",
        "description": "Press a single key or key combination, e.g. 'enter' or 'ctrl+c'.",
        "parameters": {"key": "string - the key or combo to press"},
        "confirm": True,
        "func": execute_press_key,
    },
]
