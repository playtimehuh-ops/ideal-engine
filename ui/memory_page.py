from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QListWidget,
    QListWidgetItem, QLabel, QMessageBox
)


class MemoryPage(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(QLabel("Things Alex remembers because you told it to."))

        search_row = QHBoxLayout()
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Search memories...")
        self.search_field.textChanged.connect(self.refresh)
        clear_all_btn = QPushButton("Clear All")
        clear_all_btn.setObjectName("SecondaryButton")
        clear_all_btn.clicked.connect(self._clear_all)
        search_row.addWidget(self.search_field, 1)
        search_row.addWidget(clear_all_btn)
        layout.addLayout(search_row)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget, 1)

        self.refresh()

    def refresh(self):
        query = self.search_field.text().strip()
        memories = self.db.search_memories(query) if query else self.db.get_memories()
        self.list_widget.clear()
        for m in memories:
            item = QListWidgetItem()
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(4, 4, 4, 4)
            label = QLabel(m["content"])
            label.setWordWrap(True)
            delete_btn = QPushButton("Delete")
            delete_btn.setObjectName("SecondaryButton")
            delete_btn.clicked.connect(lambda _, mid=m["id"]: self._delete(mid))
            row_layout.addWidget(label, 1)
            row_layout.addWidget(delete_btn)
            item.setSizeHint(row.sizeHint())
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, row)

    def _delete(self, memory_id):
        self.db.delete_memory(memory_id)
        self.refresh()

    def _clear_all(self):
        confirm = QMessageBox.question(
            self, "Clear all memories",
            "This will delete everything Alex remembers about you. Continue?",
        )
        if confirm == QMessageBox.Yes:
            self.db.clear_memories()
            self.refresh()
