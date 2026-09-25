"""
VoicePipeline runs everything voice-related on ONE dedicated background thread:
wake-word reaction, speech-to-text capture, calling the Assistant, and
text-to-speech playback. Keeping it on a single thread matters on Windows,
where pyttsx3's SAPI5 backend uses COM, and COM objects are picky about
which thread touches them - so every voice/TTS action always happens on the
same worker thread here.

The wake-word *detector* itself still runs on its own thread (voice/wake_word.py)
since it needs to listen continuously - but when it fires, it only enqueues an
event; the actual response work happens back here.

All UI updates happen through plain callback functions passed in at
construction; ui/main_window.py wraps those in Qt signals so widget updates
stay on the Qt thread.
"""

import queue
import threading

from voice.wake_word import WakeWordListener
from voice.speech_to_text import SpeechToText, MicrophoneUnavailableError
from voice import model_manager


class VoicePipeline(threading.Thread):
    def __init__(self, db, memory, assistant, tts, settings_getter,
                 on_state=None, on_user_text=None, on_assistant_text=None,
                 on_error=None, stop_controller=None):
        super().__init__(daemon=True)
        self.db = db
        self.memory = memory
        self.assistant = assistant
        self.tts = tts
        self.settings_getter = settings_getter  # callable -> current settings dict
        self.stop_controller = stop_controller

        self.on_state = on_state or (lambda state, detail="": None)
        self.on_user_text = on_user_text or (lambda text: None)
        self.on_assistant_text = on_assistant_text or (lambda text: None)
        self.on_error = on_error or (lambda text: None)

        self._events = queue.Queue()
        self._running = threading.Event()
        self._running.set()

        self.stt = None
        self.wake_listener = None
        self._init_stt_and_wake()

    # ------------------------------------------------------------- setup --
    def _init_stt_and_wake(self):
        if not model_manager.is_model_ready():
            self.on_error("Speech recognition model isn't downloaded yet - voice input is "
                           "unavailable until that finishes (see Settings).")
            return

        settings = self.settings_getter()
        model_dir = str(model_manager.model_path())
        mic_index = settings["voice"]["microphone_index"]

        self.stt = SpeechToText(model_dir=model_dir, microphone_index=mic_index)
        if not self.stt.ready():
            self.on_error(f"Speech recognition failed to load: {self.stt.error()}")
            return

        if settings["wake_word"]["enabled"]:
            self.wake_listener = WakeWordListener(
                model_dir=model_dir,
                phrase=settings["wake_word"]["phrase"],
                microphone_index=mic_index,
                on_detected=self._on_wake_detected,
            )
            if self.wake_listener.ready():
                self.wake_listener.start()
            else:
                self.on_error(f"Wake word detection failed to load: {self.wake_listener.error()}")
                self.wake_listener = None

    # ------------------------------------------------------ external API --
    def submit_text(self, text: str):
        """Called by the UI for typed messages or the backup mic button result."""
        self._events.put({"type": "text", "text": text})

    def trigger_manual_listen(self):
        """Backup mic button: skip the wake word, go straight to LISTENING."""
        self._events.put({"type": "manual_listen"})

    def apply_new_settings(self, settings: dict):
        if self.wake_listener:
            self.wake_listener.set_phrase(settings["wake_word"]["phrase"])
            self.wake_listener.set_microphone(settings["voice"]["microphone_index"])
            if not settings["wake_word"]["enabled"]:
                self.wake_listener.pause()
            else:
                self.wake_listener.resume()
        if self.stt:
            self.stt.set_microphone(settings["voice"]["microphone_index"])
        self.tts.update_settings(
            voice_id=settings["voice"]["voice_id"],
            rate=settings["voice"]["rate"],
            volume=settings["voice"]["volume"],
            enabled=settings["voice"]["enabled"],
        )

    def shutdown(self):
        self._running.clear()
        if self.wake_listener:
            self.wake_listener.stop()
        self._events.put({"type": "shutdown"})

    # ------------------------------------------------------------- events --
    def _on_wake_detected(self):
        self._events.put({"type": "wake"})

    # --------------------------------------------------------------- loop --
    def run(self):
        while self._running.is_set():
            try:
                event = self._events.get(timeout=0.5)
            except queue.Empty:
                continue

            if event["type"] == "shutdown":
                break
            elif event["type"] == "wake":
                self._handle_voice_turn(spoken_greeting="Yes?")
            elif event["type"] == "manual_listen":
                self._handle_voice_turn(spoken_greeting=None)
            elif event["type"] == "text":
                self._handle_text_turn(event["text"])

    # ------------------------------------------------------------ helpers --
    def _handle_voice_turn(self, spoken_greeting):
        if self.stop_controller and self.stop_controller.is_stopped():
            self.stop_controller.reset()

        if not self.stt or not self.stt.ready():
            self.on_error("Voice input isn't available right now.")
            self.on_state("READY")
            return

        if self.wake_listener:
            self.wake_listener.pause()

        self.on_state("LISTENING")
        if spoken_greeting:
            self.tts.speak(spoken_greeting)

        try:
            text = self.stt.listen_for_utterance(
                stop_event=self.stop_controller.event if self.stop_controller else None
            )
        except MicrophoneUnavailableError:
            self.on_error("Microphone unavailable. Please select another microphone in Settings.")
            text = ""

        if text:
            self.on_user_text(text)
            self._run_assistant_and_speak(text)
        else:
            self.on_state("READY")

        if self.wake_listener:
            self.wake_listener.resume()

    def _handle_text_turn(self, text: str):
        self.on_user_text(text)
        self._run_assistant_and_speak(text)

    def _run_assistant_and_speak(self, text: str):
        settings = self.settings_getter()
        try:
            reply = self.assistant.handle_utterance(text, temperature=settings["ai"]["temperature"])
        except Exception as e:
            reply = f"Something went wrong on my end: {e}"

        if self.stop_controller and self.stop_controller.is_stopped():
            self.on_state("READY")
            self.stop_controller.reset()
            return

        self.on_assistant_text(reply)
        self.on_state("SPEAKING")
        self.tts.speak(reply)
        self.on_state("READY")
