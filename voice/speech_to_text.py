"""
Offline speech-to-text using Vosk (local model, no cloud, no per-request cost).

SpeechToText.listen_for_utterance() records from the microphone until the user
stops talking (simple energy-based silence detection) and returns the
recognized text. Used both for normal requests and (via wake_word.py) for
short-window wake-phrase detection.
"""

import json
import queue
import threading

SAMPLE_RATE = 16000
SILENCE_RMS_THRESHOLD = 500       # tune-able; int16 PCM energy threshold
SILENCE_DURATION_SECONDS = 1.0    # stop after this much continuous quiet
MAX_UTTERANCE_SECONDS = 15


class MicrophoneUnavailableError(Exception):
    pass


def list_microphones():
    """Returns [{index, name}] of input-capable audio devices."""
    try:
        import sounddevice as sd
    except Exception:
        return []
    devices = []
    try:
        for i, d in enumerate(sd.query_devices()):
            if d.get("max_input_channels", 0) > 0:
                devices.append({"index": i, "name": d.get("name", f"Device {i}")})
    except Exception:
        pass
    return devices


class SpeechToText:
    def __init__(self, model_dir: str, microphone_index=None):
        self.microphone_index = microphone_index
        self._model = None
        self._model_dir = model_dir
        self._load_error = None
        self._load_model()

    def _load_model(self):
        try:
            from vosk import Model
            self._model = Model(self._model_dir)
        except Exception as e:
            self._model = None
            self._load_error = str(e)

    def ready(self) -> bool:
        return self._model is not None

    def error(self):
        return self._load_error

    def set_microphone(self, index):
        self.microphone_index = index

    def listen_for_utterance(self, stop_event: threading.Event = None) -> str:
        """
        Blocking. Records until ~1s of silence (or MAX_UTTERANCE_SECONDS) and
        returns the recognized text, or "" if nothing usable was captured.
        Raises MicrophoneUnavailableError if the mic can't be opened.
        """
        if not self.ready():
            return ""

        import sounddevice as sd
        import numpy as np
        from vosk import KaldiRecognizer

        recognizer = KaldiRecognizer(self._model, SAMPLE_RATE)
        audio_q = queue.Queue()

        def callback(indata, frames, time_info, status):
            audio_q.put(bytes(indata))

        try:
            stream = sd.RawInputStream(
                samplerate=SAMPLE_RATE,
                blocksize=8000,
                dtype="int16",
                channels=1,
                device=self.microphone_index,
                callback=callback,
            )
        except Exception as e:
            raise MicrophoneUnavailableError(str(e))

        silent_seconds = 0.0
        elapsed = 0.0
        chunk_seconds = 8000 / SAMPLE_RATE

        with stream:
            while elapsed < MAX_UTTERANCE_SECONDS:
                if stop_event is not None and stop_event.is_set():
                    break
                try:
                    data = audio_q.get(timeout=1.0)
                except queue.Empty:
                    break

                recognizer.AcceptWaveform(data)

                samples = np.frombuffer(data, dtype=np.int16)
                rms = float(np.sqrt(np.mean(samples.astype(np.float64) ** 2))) if len(samples) else 0.0
                if rms < SILENCE_RMS_THRESHOLD:
                    silent_seconds += chunk_seconds
                else:
                    silent_seconds = 0.0

                elapsed += chunk_seconds
                if silent_seconds >= SILENCE_DURATION_SECONDS and elapsed > chunk_seconds * 2:
                    break

        try:
            result = json.loads(recognizer.FinalResult())
            return (result.get("text") or "").strip()
        except Exception:
            return ""
