"""
open_application tool.

Maps a handful of common app names to how to actually launch them on Windows.
Falls back to os.startfile(name), which works for anything on the PATH or any
registered app name (e.g. "notepad", "calc"). This is intentionally NOT
arbitrary shell execution - there is no way to pass shell metacharacters or
arbitrary commands through this tool, only a plain app name/alias.
"""

import os
import subprocess
import shutil

# Friendly aliases -> the actual executable/registered name Windows understands.
KNOWN_APPS = {
    "chrome": "chrome",
    "google chrome": "chrome",
    "edge": "msedge",
    "microsoft edge": "msedge",
    "notepad": "notepad",
    "calculator": "calc",
    "calc": "calc",
    "explorer": "explorer",
    "file explorer": "explorer",
    "word": "winword",
    "microsoft word": "winword",
    "excel": "excel",
    "microsoft excel": "excel",
    "paint": "mspaint",
    "cmd": "cmd",
    "command prompt": "cmd",
    "terminal": "wt",
    "settings": "ms-settings:",
}


def _launch(target: str) -> None:
    if os.name == "nt":
        os.startfile(target)  # noqa: S606 - Windows-only, no shell involved
    else:
        # Best-effort so the module can still be imported/tested off Windows.
        resolved = shutil.which(target)
        if resolved:
            subprocess.Popen([resolved])
        else:
            raise FileNotFoundError(target)


def execute(args: dict) -> str:
    app_name = (args.get("app_name") or "").strip().lower()
    if not app_name:
        return "I didn't catch which application to open."

    target = KNOWN_APPS.get(app_name, app_name)
    try:
        _launch(target)
        return f"Opened {app_name}."
    except FileNotFoundError:
        return f"I couldn't find an application called '{app_name}' on this computer."
    except OSError as e:
        return f"I couldn't open {app_name}: {e}"


TOOLS = [
    {
        "name": "open_application",
        "description": "Open a known desktop application by name, e.g. Chrome, Notepad, Calculator.",
        "parameters": {
            "app_name": "string - the application to open, e.g. 'chrome' or 'notepad'",
        },
        "confirm": False,
        "func": execute,
    }
]
