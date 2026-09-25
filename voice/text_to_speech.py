"""
Offline text-to-speech via pyttsx3, which wraps the voices already installed
on Windows (SAPI5). No API key, no internet connection, no per-request cost.
"""

import threading


class TextToSpeech:
    def __init__(self, voice_id=None, rate=175, volume=1.0, enabled=True):
        self.enabled = enabled
        self._lock = threading.Lock()
        self._engine = None
        self._stop_flag = threading.Event()
        self.voice_id = voice_id
        self.rate = rate
        self.volume = volume
        self._init_engine()

    def _init_engine(self):
        try:
            import pyttsx3
            self._engine = pyttsx3.init()
            self._apply_settings()
        except Exception:
            self._engine = None  # TTS unavailable; app keeps running text-only.

    def _apply_settings(self):
        if not self._engine:
            return
        try:
            self._engine.setProperty("rate", self.rate)
            self._engine.setProperty("volume", max(0.0, min(1.0, self.volume)))
            if self.voice_id:
                self._engine.setProperty("voice", self.voice_id)
        except Exception:
            pass

    def available(self) -> bool:
        return self._engine is not None

    def list_voices(self):
        """Returns [{id, name}] of voices installed on this Windows machine."""
        if not self._engine:
            return []
        try:
            return [{"id": v.id, "name": v.name} for v in self._engine.getProperty("voices")]
        except Exception:
            return []

    def update_settings(self, voice_id=None, rate=None, volume=None, enabled=None):
        if voice_id is not None:
            self.voice_id = voice_id
        if rate is not None:
            self.rate = rate
        if volume is not None:
            self.volume = volume
        if enabled is not None:
            self.enabled = enabled
        self._apply_settings()

    def speak(self, text: str):
        """Blocking call - run this on a worker thread, not the Qt UI thread."""
        if not self.enabled or not text:
            return
        if not self._engine:
            return
        self._stop_flag.clear()
        with self._lock:
            try:
                self._engine.say(text)
                self._engine.runAndWait()
            except Exception:
                pass

    def stop(self):
        """Called by the STOP button. Best-effort - pyttsx3's stop cuts speech quickly."""
        self._stop_flag.set()
        if self._engine:
            try:
                self._engine.stop()
            except Exception:
                pass
