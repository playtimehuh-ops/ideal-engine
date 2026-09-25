"""
screenshot tool - read-only, so it does not require confirmation.
Saves into the app's data folder under /screenshots and returns the path.
"""

from datetime import datetime
from pathlib import Path

from config.settings import data_dir


def execute(args: dict) -> str:
    try:
        import pyautogui
    except Exception as e:
        return f"Screenshots aren't available: {e}"

    folder = data_dir() / "screenshots"
    folder.mkdir(parents=True, exist_ok=True)
    filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    path = folder / filename

    try:
        image = pyautogui.screenshot()
        image.save(str(path))
    except Exception as e:
        return f"I wasn't able to take a screenshot: {e}"

    return f"Took a screenshot and saved it to {path}."


TOOLS = [
    {
        "name": "screenshot",
        "description": "Take a screenshot of the user's screen right now.",
        "parameters": {},
        "confirm": False,
        "func": execute,
    }
]
