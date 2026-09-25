"""
Manages the offline Vosk speech-recognition model.

Vosk needs a model folder on disk (~40MB for the small English model). We
don't bundle it inside the app - instead, on first run, we download it once
into the app's data folder and reuse it forever after. This is the "clear
first-run download/setup system" the spec asks for when a local model is
required. If there's no internet on first run, Alex explains that clearly
instead of crashing.
"""

import zipfile
import shutil
import requests
from pathlib import Path

from config.settings import data_dir

MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
MODEL_DIR_NAME = "vosk-model-small-en-us-0.15"


def model_path() -> Path:
    return data_dir() / "models" / MODEL_DIR_NAME


def is_model_ready() -> bool:
    path = model_path()
    return path.exists() and any(path.iterdir()) if path.exists() else False


def download_model(progress_callback=None) -> bool:
    """
    Downloads and extracts the Vosk model. progress_callback(fraction: float)
    is called periodically if provided. Returns True on success.
    """
    models_dir = data_dir() / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    zip_path = models_dir / "model.zip"

    try:
        with requests.get(MODEL_URL, stream=True, timeout=60) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0)) or None
            downloaded = 0
            with open(zip_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 256):
                    if not chunk:
                        continue
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total:
                        progress_callback(min(0.9, downloaded / total * 0.9))

        if progress_callback:
            progress_callback(0.92)

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(models_dir)

        zip_path.unlink(missing_ok=True)

        if progress_callback:
            progress_callback(1.0)
        return is_model_ready()

    except Exception:
        # Leave things in a clean state so the user can retry.
        if zip_path.exists():
            zip_path.unlink(missing_ok=True)
        return False
