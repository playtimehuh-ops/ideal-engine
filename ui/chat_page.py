from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QLabel
)
from PySide6.QtCore import Signal


class ChatPage(QWidget):
    message_submitted = Signal(str)
    mic_button_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        self.transcript = QTextEdit()
        self.transcript.setObjectName("Transcript")
        self.transcript.setReadOnly(True)
        layout.addWidget(self.transcript, 1)

        input_row = QHBoxLayout()
        self.mic_button = QPushButton("\U0001F399")  # microphone emoji, backup input
        self.mic_button.setObjectName("SecondaryButton")
        self.mic_button.setFixedWidth(48)
        self.mic_button.setToolTip("Backup: click to speak one request without saying the wake word")
        self.mic_button.clicked.connect(self.mic_button_clicked.emit)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type a message... (voice is the main way to talk to Alex)")
        self.input_field.returnPressed.connect(self._submit)

        self.send_button = QPushButton("SEND")
        self.send_button.setObjectName("PrimaryButton")
        self.send_button.clicked.connect(self._submit)

        input_row.addWidget(self.mic_button)
        input_row.addWidget(self.input_field, 1)
        input_row.addWidget(self.send_button)
        layout.addLayout(input_row)

    def _submit(self):
        text = self.input_field.text().strip()
        if not text:
            return
        self.input_field.clear()
        self.message_submitted.emit(text)

    def append_user(self, text: str):
        self.transcript.append(f'<p style="color:#8A90A0;margin:4px 0;">You</p>'
                                f'<p style="margin:0 0 10px 0;">{_escape(text)}</p>')

    def append_assistant(self, text: str):
        self.transcript.append(f'<p style="color:#2F8FFF;margin:4px 0;">Alex</p>'
                                f'<p style="margin:0 0 10px 0;">{_escape(text)}</p>')

    def append_system(self, text: str):
        self.transcript.append(f'<p style="color:#FF4D4F;margin:4px 0 10px 0;"><i>{_escape(text)}</i></p>')


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
    )
