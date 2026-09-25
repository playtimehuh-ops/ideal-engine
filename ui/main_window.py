import json

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QStackedWidget, QMessageBox
)
from PySide6.QtCore import Qt, QObject, Signal, QSize
from PySide6.QtGui import QIcon

from config import settings as settings_module
from storage.database import Database
from core.memory import MemoryManager
from core.safety import StopController, ConfirmationGate
from core.assistant import Assistant
from core.voice_pipeline import VoicePipeline
from ai.openrouter import OpenRouterProvider

from ui.theme import stylesheet, STATUS_COLORS
from ui.visualizer import VoiceVisualizer
from ui.chat_page import ChatPage
from ui.memory_page import MemoryPage
from ui.activity_page import ActivityPage
from ui.settings_page import SettingsPage
from voice.text_to_speech import TextToSpeech


class _Bridge(QObject):
    """Marshals worker-thread callbacks onto the Qt (main) thread safely."""
    state_changed = Signal(str, str)
    user_text = Signal(str)
    assistant_text = Signal(str)
    error_text = Signal(str)
    confirm_requested = Signal(str, str)  # tool_name, json args - BlockingQueuedConnection

    def __init__(self):
        super().__init__()
        self.confirm_result = False

    def handle_confirm(self, tool_name: str, args_json: str):
        try:
            args = json.loads(args_json)
        except Exception:
            args = {}
        pretty_args = ", ".join(f"{k}={v}" for k, v in args.items()) or "no parameters"
        text = f"Alex wants to run '{tool_name}' ({pretty_args}). Allow this?"
        reply = QMessageBox.question(None, "Confirm action", text,
                                      QMessageBox.Yes | QMessageBox.No)
        self.confirm_result = (reply == QMessageBox.Yes)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Alex")
        self.resize(1000, 680)

        self.settings = settings_module.get_settings()
        self.setStyleSheet(stylesheet(self.settings["appearance"]["accent_color"]))

        # --- core services -------------------------------------------------
        self.db = Database()
        self.memory = MemoryManager(self.db)
        self.stop_controller = StopController()
        self.confirmation_gate = ConfirmationGate()
        self.tts = TextToSpeech(
            voice_id=self.settings["voice"]["voice_id"],
            rate=self.settings["voice"]["rate"],
            volume=self.settings["voice"]["volume"],
            enabled=self.settings["voice"]["enabled"],
        )

        self.bridge = _Bridge()
        self.bridge.confirm_requested.connect(self.bridge.handle_confirm, Qt.BlockingQueuedConnection)
        self.confirmation_gate.show_dialog_callback = self._ask_confirmation

        self.assistant = Assistant(
            db=self.db,
            memory=self.memory,
            get_ai_provider=self._get_ai_provider,
            confirmation_gate=self.confirmation_gate,
            stop_controller=self.stop_controller,
            on_state=lambda state, detail="": self.bridge.state_changed.emit(state, detail),
            on_error=lambda msg: self.bridge.error_text.emit(msg),
        )

        self.voice_pipeline = VoicePipeline(
            db=self.db,
            memory=self.memory,
            assistant=self.assistant,
            tts=self.tts,
            settings_getter=lambda: self.settings,
            on_state=lambda state, detail="": self.bridge.state_changed.emit(state, detail),
            on_user_text=lambda text: self.bridge.user_text.emit(text),
            on_assistant_text=lambda text: self.bridge.assistant_text.emit(text),
            on_error=lambda msg: self.bridge.error_text.emit(msg),
            stop_controller=self.stop_controller,
        )

        self.bridge.state_changed.connect(self._on_state_changed)
        self.bridge.user_text.connect(self._on_user_text)
        self.bridge.assistant_text.connect(self._on_assistant_text)
        self.bridge.error_text.connect(self._on_error_text)

        self._build_ui()
        self.voice_pipeline.start()

    # ------------------------------------------------------------------ UI --
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_top_bar())

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(self._build_sidebar())

        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)

        self.pages = QStackedWidget()
        self.chat_page = ChatPage()
        self.memory_page = MemoryPage(self.db)
        self.activity_page = ActivityPage(self.db)
        self.settings_page = SettingsPage(self.tts)
        self.pages.addWidget(self.chat_page)
        self.pages.addWidget(self.memory_page)
        self.pages.addWidget(self.activity_page)
        self.pages.addWidget(self.settings_page)
        right.addWidget(self.pages, 1)

        self.chat_page.message_submitted.connect(self.voice_pipeline.submit_text)
        self.chat_page.mic_button_clicked.connect(self.voice_pipeline.trigger_manual_listen)
        self.settings_page.settings_saved.connect(self._on_settings_saved)

        right.addWidget(self._build_bottom_bar())

        body_widget = QWidget()
        body_widget.setLayout(body)
        body.addLayout(right, 1)
        root.addWidget(body_widget, 1)

        self.chat_page.append_system('Ready. Say "Hey Alex".')

    def _build_top_bar(self):
        bar = QWidget()
        bar.setObjectName("TopBar")
        bar.setFixedHeight(52)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 0, 20, 0)

        title = QLabel("ALEX")
        title.setObjectName("TitleLabel")
        layout.addWidget(title)
        layout.addStretch(1)

        self.status_pill = QLabel("● READY")
        self.status_pill.setObjectName("StatusPill")
        self.status_pill.setStyleSheet(f"color: {STATUS_COLORS['READY']};")
        layout.addWidget(self.status_pill)

        return bar

    def _build_sidebar(self):
        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(160)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(8, 16, 8, 16)
        layout.setSpacing(4)

        self.nav_buttons = []
        for i, name in enumerate(["Chat", "Memory", "Activity", "Settings"]):
            btn = QPushButton(name)
            btn.setObjectName("NavButton")
            btn.setCheckable(True)
            btn.setChecked(i == 0)
            btn.clicked.connect(lambda _, idx=i: self._switch_page(idx))
            layout.addWidget(btn)
            self.nav_buttons.append(btn)
        layout.addStretch(1)
        return sidebar

    def _build_bottom_bar(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 8, 16, 16)
        layout.setSpacing(8)

        self.visualizer = VoiceVisualizer()
        layout.addWidget(self.visualizer)

        self.status_caption = QLabel('Say "Hey Alex"')
        self.status_caption.setAlignment(Qt.AlignCenter)
        self.status_caption.setStyleSheet("color: #8A90A0;")
        layout.addWidget(self.status_caption)

        self.stop_button = QPushButton("STOP")
        self.stop_button.setObjectName("StopButton")
        self.stop_button.setMinimumHeight(44)
        self.stop_button.clicked.connect(self._on_stop_clicked)
        layout.addWidget(self.stop_button)

        return container

    def _switch_page(self, index):
        self.pages.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
        if index == 1:
            self.memory_page.refresh()
        elif index == 2:
            self.activity_page.refresh()

    # ------------------------------------------------------------- signals --
    def _on_state_changed(self, state: str, detail: str):
        color = STATUS_COLORS.get(state, "#2F8FFF")
        self.status_pill.setText(f"● {state}")
        self.status_pill.setStyleSheet(f"color: {color};")
        self.visualizer.set_state(state)

        captions = {
            "READY": 'Say "Hey Alex"',
            "LISTENING": "I'm listening...",
            "THINKING": "Thinking...",
            "SEARCHING": "Searching the web...",
            "SPEAKING": "Speaking...",
            "ACTION": f"Working on it{': ' + detail if detail else '...'}",
            "ERROR": "Something went wrong.",
        }
        self.status_caption.setText(captions.get(state, ""))

    def _on_user_text(self, text: str):
        self.chat_page.append_user(text)

    def _on_assistant_text(self, text: str):
        self.chat_page.append_assistant(text)

    def _on_error_text(self, text: str):
        self.chat_page.append_system(text)
        self._on_state_changed("ERROR", "")
        # Auto-recover the status pill back to READY shortly after, since
        # ERROR here means "that request failed", not "the app is broken".
        from PySide6.QtCore import QTimer
        QTimer.singleShot(2500, lambda: self._on_state_changed("READY", ""))

    def _on_settings_saved(self, new_settings: dict):
        self.settings = new_settings
        self.setStyleSheet(stylesheet(new_settings["appearance"]["accent_color"]))
        self.voice_pipeline.apply_new_settings(new_settings)

    def _on_stop_clicked(self):
        self.stop_controller.request_stop()
        self.tts.stop()
        self.chat_page.append_system("Stopped.")
        self._on_state_changed("READY", "")

    # -------------------------------------------------------------- helpers --
    def _get_ai_provider(self):
        api_key = settings_module.get_api_key()
        if not api_key:
            return None
        return OpenRouterProvider(api_key=api_key, model=self.settings["ai"]["model"])

    def _ask_confirmation(self, tool_name: str, args: dict) -> bool:
        self.bridge.confirm_requested.emit(tool_name, json.dumps(args))
        return self.bridge.confirm_result

    def closeEvent(self, event):
        self.voice_pipeline.shutdown()
        self.db.close()
        super().closeEvent(event)
