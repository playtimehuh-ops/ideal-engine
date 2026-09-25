from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QPushButton, QHBoxLayout, QLabel


class ActivityPage(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()
        header.addWidget(QLabel("What Alex has done recently - wake events, tool calls, errors."))
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setObjectName("SecondaryButton")
        refresh_btn.clicked.connect(self.refresh)
        header.addStretch(1)
        header.addWidget(refresh_btn)
        layout.addLayout(header)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget, 1)

        self.refresh()

    def refresh(self):
        self.list_widget.clear()
        for entry in self.db.get_activity(200):
            ts = entry["created_at"].replace("T", " ")
            text = f"[{ts}]  {entry['event']}"
            if entry["detail"]:
                text += f"  —  {entry['detail']}"
            self.list_widget.addItem(QListWidgetItem(text))
