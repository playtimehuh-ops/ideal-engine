"""
A light-weight animated bar visualizer. Idles with a slow pulse at READY,
and animates more actively during LISTENING/SPEAKING. Deliberately simple -
this is drawn with QPainter on a timer, no video/GPU shader work, so it stays
cheap on CPU.
"""

import math
import random

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor

from ui.theme import STATUS_COLORS

BAR_COUNT = 24


class VoiceVisualizer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(64)
        self._phase = 0.0
        self._state = "READY"
        self._levels = [0.1] * BAR_COUNT
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(60)  # ~16fps - smooth enough, cheap enough

    def set_state(self, state: str):
        self._state = state
        self.update()

    def _tick(self):
        self._phase += 0.15
        active = self._state in ("LISTENING", "SPEAKING")
        thinking = self._state in ("THINKING", "SEARCHING", "ACTION")

        for i in range(BAR_COUNT):
            base = 0.15 + 0.10 * math.sin(self._phase + i * 0.4)
            if active:
                target = 0.25 + random.random() * 0.75
            elif thinking:
                target = 0.20 + 0.15 * math.sin(self._phase * 1.5 + i * 0.6)
            else:
                target = base
            self._levels[i] += (target - self._levels[i]) * 0.35
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        color = QColor(STATUS_COLORS.get(self._state, "#2F8FFF"))

        w = self.width()
        h = self.height()
        bar_w = w / (BAR_COUNT * 1.6)
        gap = bar_w * 0.6
        total_w = BAR_COUNT * bar_w + (BAR_COUNT - 1) * gap
        x = (w - total_w) / 2

        for level in self._levels:
            bar_h = max(4.0, level * (h * 0.8))
            y = (h - bar_h) / 2
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(int(x), int(y), int(bar_w), int(bar_h), 3, 3)
            x += bar_w + gap
