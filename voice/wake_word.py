"""
Local wake-word detection.

Runs a background thread that continuously transcribes short rolling windows
of microphone audio with the same offline Vosk model used for full requests,
and checks whether the wake phrase appears. Nothing is sent anywhere - it's
the same local model, just used on short buffers. Full-sentence recognition
of the user's actual request only starts *after* the wake word fires (see
core/assistant.py), so no request audio is processed until the user has
deliberately triggered Alex.

This thread must be paused (via pause()) while SpeechToText is doing its own
recording of the user's request, so the two don't fight over the microphone.
"""

import json
import queue
import threading
import time

SAMPLE_RATE = 16000
BLOCK_FRAMES = 4000  # ~0.25s per block at 16kHz


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


class WakeWordListener(threading.Thread):
    def __init__(self, model_dir: str, phrase: str, microphone_index, on_detected):
        super().__init__(daemon=True)
        self.phrase = _normalize(phrase or "hey alex")
        self.microphone_index = microphone_index
        self.on_detected = on_detected

        self._model = None
        self._load_error = None
        self._running = threading.Event()
        self._running.set()
        self._paused = threading.Event()  # set() == paused

        self._load_model(model_dir)

    def _load_model(self, model_dir):
        try:
            from vosk import Model
            self._model = Model(model_dir)
        except Exception as e:
            self._load_error = str(e)

    def ready(self):
        return self._model is not None

    def error(self):
        return self._load_error

    def pause(self):
        self._paused.set()

    def resume(self):
        self._paused.clear()

    def stop(self):
        self._running.clear()

    def set_microphone(self, index):
        self.microphone_index = index

    def set_phrase(self, phrase):
        self.phrase = _normalize(phrase or "hey alex")

    def run(self):
        if not self.ready():
            return

        try:
            import sounddevice as sd
            from vosk import KaldiRecognizer
        except Exception as e:
            self._load_error = str(e)
            return

        while self._running.is_set():
            if self._paused.is_set():
                time.sleep(0.2)
                continue

            recognizer = KaldiRecognizer(self._model, SAMPLE_RATE)
            audio_q = queue.Queue()

            def callback(indata, frames, time_info, status):
                audio_q.put(bytes(indata))

            try:
                stream = sd.RawInputStream(
                    samplerate=SAMPLE_RATE,
                    blocksize=BLOCK_FRAMES,
                    dtype="int16",
                    channels=1,
                    device=self.microphone_index,
                    callback=callback,
                )
            except Exception as e:
                self._load_error = str(e)
                time.sleep(2.0)  # retry loop rather than crashing the thread
                continue

            with stream:
                # Listen in short rolling windows so a wake word is caught
                # quickly without ever needing to send audio anywhere.
                window_seconds = 0.0
                while self._running.is_set() and not self._paused.is_set():
                    try:
                        data = audio_q.get(timeout=0.5)
                    except queue.Empty:
                        continue

                    if recognizer.AcceptWaveform(data):
                        text = _normalize(json.loads(recognizer.Result()).get("text", ""))
                    else:
                        text = _normalize(json.loads(recognizer.PartialResult()).get("partial", ""))

                    if self.phrase and self.phrase in text:
                        recognizer.Reset()
                        try:
                            self.on_detected()
                        except Exception:
                            pass
                        # Let the assistant pause() us; break out to re-check.
                        break

                    window_seconds += BLOCK_FRAMES / SAMPLE_RATE
                    if window_seconds > 8.0:
                        recognizer.Reset()
                        window_seconds = 0.0
