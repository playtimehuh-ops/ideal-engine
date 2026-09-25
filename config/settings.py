"""
Settings storage for Alex.

Non-secret settings live in a plain JSON file under the user's app-data folder.
The OpenRouter API key is NEVER written to that file or to source code - it is
stored using the OS-level secure credential store via the `keyring` package
(Windows Credential Locker on Windows).
"""

import json
import os
import copy
from pathlib import Path

try:
    import keyring
    _KEYRING_OK = True
except Exception:
    # keyring can fail to import/initialize on some minimal systems.
    # We degrade gracefully instead of crashing the whole app.
    _KEYRING_OK = False

APP_NAME = "Alex"
KEYRING_SERVICE = "AlexAssistant"
KEYRING_USERNAME = "openrouter_api_key"

DEFAULT_SETTINGS = {
    "first_run_complete": False,
    "ai": {
        "provider": "openrouter",
        # NOTE: OpenRouter's roster of free models changes over time.
        # This is a placeholder sane default - check https://openrouter.ai/models
        # (filter by "free") and update this in Settings if it stops working.
        "model": "meta-llama/llama-3.3-70b-instruct:free",
        "temperature": 0.7,
    },
    "voice": {
        "microphone_index": None,   # None = system default
        "voice_id": None,           # None = system default TTS voice
        "volume": 1.0,              # 0.0 - 1.0
        "rate": 175,                # words per minute, pyttsx3 default-ish
        "enabled": True,
    },
    "wake_word": {
        "enabled": True,
        "phrase": "hey alex",
    },
    "web": {
        "enabled": True,
    },
    "appearance": {
        "dark_mode": True,
        "accent_color": "#2F8FFF",  # electric blue
        "animation_level": "normal",  # off | reduced | normal
    },
    "startup": {
        "start_with_windows": False,
        "start_minimized": False,
    },
}


def _app_data_dir() -> Path:
    """Return (and create) the per-user folder Alex stores its files in."""
    if os.name == "nt":
        base = os.environ.get("APPDATA") or str(Path.home())
    else:
        # Lets the app run for development/testing on non-Windows too.
        base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    path = Path(base) / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def _settings_path() -> Path:
    return _app_data_dir() / "settings.json"


def data_dir() -> Path:
    """Public accessor other modules use for the DB file, downloaded models, logs, etc."""
    return _app_data_dir()


def _deep_merge(base: dict, override: dict) -> dict:
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def get_settings() -> dict:
    """Load settings, merged over defaults so new fields never crash old configs."""
    path = _settings_path()
    if not path.exists():
        return copy.deepcopy(DEFAULT_SETTINGS)
    try:
        with open(path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        return _deep_merge(DEFAULT_SETTINGS, loaded)
    except (json.JSONDecodeError, OSError):
        # Corrupt settings file shouldn't take the app down.
        return copy.deepcopy(DEFAULT_SETTINGS)


def save_settings(settings: dict) -> None:
    path = _settings_path()
    tmp_path = path.with_suffix(".json.tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
    tmp_path.replace(path)  # atomic-ish on both platforms


# ---------------------------------------------------------------------------
# API key handling (kept completely separate from the JSON file)
# ---------------------------------------------------------------------------

def get_api_key() -> str:
    """Return the stored OpenRouter API key, or '' if none is set."""
    if not _KEYRING_OK:
        return os.environ.get("ALEX_OPENROUTER_API_KEY", "")
    try:
        value = keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
        return value or ""
    except Exception:
        return ""


def set_api_key(key: str) -> bool:
    """Store the API key securely. Returns True on success."""
    key = (key or "").strip()
    if not _KEYRING_OK:
        return False
    try:
        if key:
            keyring.set_password(KEYRING_SERVICE, KEYRING_USERNAME, key)
        else:
            try:
                keyring.delete_password(KEYRING_SERVICE, KEYRING_USERNAME)
            except Exception:
                pass
        return True
    except Exception:
        return False


def mask_key(key: str) -> str:
    """Never show a full key in the UI - only the last 4 characters."""
    key = key or ""
    if len(key) <= 4:
        return "*" * len(key)
    return "*" * (len(key) - 4) + key[-4:]


def keyring_available() -> bool:
    return _KEYRING_OK
