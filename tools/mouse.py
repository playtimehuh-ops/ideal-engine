"""
click tool. Confirmed before running (see core/safety.CONFIRMATION_REQUIRED_TOOLS).
"""


def execute(args: dict) -> str:
    try:
        import pyautogui
    except Exception as e:
        return f"Mouse control isn't available: {e}"

    try:
        x = int(args.get("x"))
        y = int(args.get("y"))
    except (TypeError, ValueError):
        return "I need valid x and y coordinates to click."

    button = (args.get("button") or "left").lower()
    if button not in ("left", "right", "middle"):
        button = "left"

    try:
        screen_w, screen_h = pyautogui.size()
        x = max(0, min(x, screen_w - 1))
        y = max(0, min(y, screen_h - 1))
        pyautogui.click(x=x, y=y, button=button)
    except Exception as e:
        return f"I couldn't click there: {e}"

    return f"Clicked at ({x}, {y})."


TOOLS = [
    {
        "name": "click",
        "description": "Click the mouse at a specific screen coordinate.",
        "parameters": {
            "x": "integer - horizontal pixel coordinate",
            "y": "integer - vertical pixel coordinate",
            "button": "string, optional - 'left' (default), 'right', or 'middle'",
        },
        "confirm": True,
        "func": execute,
    }
]
