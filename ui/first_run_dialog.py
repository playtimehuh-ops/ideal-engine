from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QProgressBar, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal

from config import settings as settings_module
from voice.speech_to_text import list_microphones
from voice import model_manager


class ModelDownloadThread(QThread):
    progress = Signal(float)
    finished_ok = Signal(bool)

    def run(self):
        ok = model_manager.download_model(progress_callback=self.progress.emit)
        self.finished_ok.emit(ok)


class FirstRunDialog(QDialog):
    def __init__(self, tts_for_voice_list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome to Alex")
        self.setMinimumWidth(420)
        self._tts = tts_for_voice_list
        self._download_thread = None

        layout = QVBoxLayout(self)
        title = QLabel("WELCOME TO ALEX")
        title.setStyleSheet("font-size: 20px; font-weight: 700; letter-spacing: 2px;")
        layout.addWidget(title)
        subtitle = QLabel("Your personal, voice-first AI assistant.")
        subtitle.setStyleSheet("color: #8A90A0;")
        layout.addWidget(subtitle)

        form = QFormLayout()
        self.api_key_field = QLineEdit()
        self.api_key_field.setEchoMode(QLineEdit.Password)
        self.api_key_field.setPlaceholderText("Paste your OpenRouter API key (you can add this later too)")
        form.addRow("OpenRouter API Key", self.api_key_field)

        self.mic_combo = QComboBox()
        self.mic_combo.addItem("System default", None)
        for m in list_microphones():
            self.mic_combo.addItem(m["name"], m["index"])
        form.addRow("Microphone", self.mic_combo)

        self.voice_combo = QComboBox()
        self.voice_combo.addItem("System default", None)
        for v in self._tts.list_voices():
            self.voice_combo.addItem(v["name"], v["id"])
        form.addRow("Voice", self.voice_combo)

        layout.addLayout(form)

        self.status_label = QLabel(
            "Alex needs a one-time ~40MB download for offline speech recognition."
        )
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.start_button = QPushButton("START ALEX")
        self.start_button.setObjectName("PrimaryButton")
        self.start_button.clicked.connect(self._on_start_clicked)
        layout.addWidget(self.start_button)

        if model_manager.is_model_ready():
            self.progress_bar.setValue(100)
            self.status_label.setText("Speech recognition model already downloaded.")

    def _on_start_clicked(self):
        self._save_initial_settings()

        if model_manager.is_model_ready():
            self.accept()
            return

        self.start_button.setEnabled(False)
        self.status_label.setText("Downloading offline speech recognition model...")
        self._download_thread = ModelDownloadThread()
        self._download_thread.progress.connect(lambda f: self.progress_bar.setValue(int(f * 100)))
        self._download_thread.finished_ok.connect(self._on_download_done)
        self._download_thread.start()

    def _on_download_done(self, ok: bool):
        self.start_button.setEnabled(True)
        if ok:
            self.accept()
        else:
            QMessageBox.warning(
                self, "Download failed",
                "Alex couldn't download the speech recognition model. Check your internet "
                "connection and try again - Alex will still open and work by text in the "
                "meantime, but voice won't be available until this succeeds.",
            )
            self.accept()  # let them into the app anyway; voice will just be disabled

    def _save_initial_settings(self):
        s = settings_module.get_settings()
        key = self.api_key_field.text().strip()
        if key:
            settings_module.set_api_key(key)
        s["voice"]["microphone_index"] = self.mic_combo.currentData()
        s["voice"]["voice_id"] = self.voice_combo.currentData()
        s["first_run_complete"] = True
        settings_module.save_settings(s)
