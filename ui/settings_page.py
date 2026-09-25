from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QGroupBox, QLineEdit, QComboBox,
    QCheckBox, QPushButton, QDoubleSpinBox, QSpinBox, QLabel, QScrollArea,
    QMessageBox
)
from PySide6.QtCore import Signal

from config import settings as settings_module
from voice.speech_to_text import list_microphones


class SettingsPage(QWidget):
    # Emitted after Save, so MainWindow can re-create the AI client / TTS / wake listener.
    settings_saved = Signal(dict)

    def __init__(self, tts_for_voice_list, parent=None):
        super().__init__(parent)
        self._tts = tts_for_voice_list
        self.settings = settings_module.get_settings()

        outer = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        outer.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        layout.addWidget(self._build_ai_group())
        layout.addWidget(self._build_voice_group())
        layout.addWidget(self._build_wake_word_group())
        layout.addWidget(self._build_web_group())
        layout.addWidget(self._build_appearance_group())
        layout.addWidget(self._build_startup_group())

        save_btn = QPushButton("Save Settings")
        save_btn.setObjectName("PrimaryButton")
        save_btn.clicked.connect(self._save)
        layout.addWidget(save_btn)
        layout.addStretch(1)

    # ---------------------------------------------------------------- AI --
    def _build_ai_group(self):
        box = QGroupBox("AI")
        form = QFormLayout(box)

        self.api_key_field = QLineEdit()
        current_key = settings_module.get_api_key()
        self.api_key_field.setPlaceholderText(
            "Currently set (hidden)" if current_key else "Paste your OpenRouter API key"
        )
        self.api_key_field.setEchoMode(QLineEdit.Password)
        form.addRow("OpenRouter API key", self.api_key_field)

        note = QLabel(
            "Get a key at openrouter.ai. Free-tier models are subject to rate limits and "
            "availability changes - they are not unlimited."
        )
        note.setWordWrap(True)
        form.addRow("", note)

        self.model_field = QLineEdit(self.settings["ai"]["model"])
        self.model_field.setPlaceholderText("e.g. meta-llama/llama-3.3-70b-instruct:free")
        form.addRow("Model", self.model_field)

        self.temperature_field = QDoubleSpinBox()
        self.temperature_field.setRange(0.0, 1.5)
        self.temperature_field.setSingleStep(0.1)
        self.temperature_field.setValue(self.settings["ai"]["temperature"])
        form.addRow("Temperature", self.temperature_field)

        return box

    # ------------------------------------------------------------- Voice --
    def _build_voice_group(self):
        box = QGroupBox("Voice")
        form = QFormLayout(box)

        self.mic_combo = QComboBox()
        self.mic_combo.addItem("System default", None)
        for m in list_microphones():
            self.mic_combo.addItem(m["name"], m["index"])
        current_mic = self.settings["voice"]["microphone_index"]
        if current_mic is not None:
            idx = self.mic_combo.findData(current_mic)
            if idx >= 0:
                self.mic_combo.setCurrentIndex(idx)
        form.addRow("Microphone", self.mic_combo)

        self.voice_combo = QComboBox()
        self.voice_combo.addItem("System default", None)
        for v in self._tts.list_voices():
            self.voice_combo.addItem(v["name"], v["id"])
        current_voice = self.settings["voice"]["voice_id"]
        if current_voice:
            idx = self.voice_combo.findData(current_voice)
            if idx >= 0:
                self.voice_combo.setCurrentIndex(idx)
        form.addRow("TTS Voice", self.voice_combo)

        self.volume_field = QDoubleSpinBox()
        self.volume_field.setRange(0.0, 1.0)
        self.volume_field.setSingleStep(0.1)
        self.volume_field.setValue(self.settings["voice"]["volume"])
        form.addRow("Volume", self.volume_field)

        self.rate_field = QSpinBox()
        self.rate_field.setRange(80, 300)
        self.rate_field.setValue(self.settings["voice"]["rate"])
        form.addRow("Speech rate (wpm)", self.rate_field)

        self.voice_enabled_check = QCheckBox("Speak responses out loud")
        self.voice_enabled_check.setChecked(self.settings["voice"]["enabled"])
        form.addRow("", self.voice_enabled_check)

        return box

    # --------------------------------------------------------- Wake word --
    def _build_wake_word_group(self):
        box = QGroupBox("Wake Word")
        form = QFormLayout(box)

        self.wake_enabled_check = QCheckBox("Enable wake word (\"Hey Alex\")")
        self.wake_enabled_check.setChecked(self.settings["wake_word"]["enabled"])
        form.addRow("", self.wake_enabled_check)

        self.wake_phrase_field = QLineEdit(self.settings["wake_word"]["phrase"])
        form.addRow("Wake phrase", self.wake_phrase_field)

        return box

    # ------------------------------------------------------------- Web --
    def _build_web_group(self):
        box = QGroupBox("Web")
        form = QFormLayout(box)
        self.web_enabled_check = QCheckBox("Allow Alex to search the web when needed")
        self.web_enabled_check.setChecked(self.settings["web"]["enabled"])
        form.addRow("", self.web_enabled_check)
        return box

    # --------------------------------------------------------- Appearance --
    def _build_appearance_group(self):
        box = QGroupBox("Appearance")
        form = QFormLayout(box)

        self.dark_mode_check = QCheckBox("Dark mode")
        self.dark_mode_check.setChecked(self.settings["appearance"]["dark_mode"])
        form.addRow("", self.dark_mode_check)

        self.accent_field = QLineEdit(self.settings["appearance"]["accent_color"])
        form.addRow("Accent color (hex)", self.accent_field)

        self.animation_combo = QComboBox()
        self.animation_combo.addItems(["off", "reduced", "normal"])
        self.animation_combo.setCurrentText(self.settings["appearance"]["animation_level"])
        form.addRow("Animation level", self.animation_combo)

        return box

    # ------------------------------------------------------------ Startup --
    def _build_startup_group(self):
        box = QGroupBox("Startup")
        form = QFormLayout(box)

        self.start_with_windows_check = QCheckBox("Start Alex with Windows")
        self.start_with_windows_check.setChecked(self.settings["startup"]["start_with_windows"])
        form.addRow("", self.start_with_windows_check)

        self.start_minimized_check = QCheckBox("Start minimized")
        self.start_minimized_check.setChecked(self.settings["startup"]["start_minimized"])
        form.addRow("", self.start_minimized_check)

        return box

    # ---------------------------------------------------------------- Save --
    def _save(self):
        new_key = self.api_key_field.text().strip()
        if new_key:
            ok = settings_module.set_api_key(new_key)
            if not ok:
                QMessageBox.warning(self, "Couldn't save key",
                                     "Alex couldn't reach the system's secure credential store. "
                                     "The key was not saved.")
            self.api_key_field.clear()
            self.api_key_field.setPlaceholderText("Currently set (hidden)")

        self.settings["ai"]["model"] = self.model_field.text().strip() or self.settings["ai"]["model"]
        self.settings["ai"]["temperature"] = self.temperature_field.value()

        self.settings["voice"]["microphone_index"] = self.mic_combo.currentData()
        self.settings["voice"]["voice_id"] = self.voice_combo.currentData()
        self.settings["voice"]["volume"] = self.volume_field.value()
        self.settings["voice"]["rate"] = self.rate_field.value()
        self.settings["voice"]["enabled"] = self.voice_enabled_check.isChecked()

        self.settings["wake_word"]["enabled"] = self.wake_enabled_check.isChecked()
        self.settings["wake_word"]["phrase"] = self.wake_phrase_field.text().strip() or "hey alex"

        self.settings["web"]["enabled"] = self.web_enabled_check.isChecked()

        self.settings["appearance"]["dark_mode"] = self.dark_mode_check.isChecked()
        self.settings["appearance"]["accent_color"] = self.accent_field.text().strip() or "#2F8FFF"
        self.settings["appearance"]["animation_level"] = self.animation_combo.currentText()

        self.settings["startup"]["start_with_windows"] = self.start_with_windows_check.isChecked()
        self.settings["startup"]["start_minimized"] = self.start_minimized_check.isChecked()

        settings_module.save_settings(self.settings)
        self.settings_saved.emit(self.settings)
        QMessageBox.information(self, "Saved", "Settings saved.")
