"""
Original dark UI theme for Alex - charcoal + electric blue, deliberately not
a JARVIS/Iron-Man style HUD. No purple, no heavy gradients.
"""

BG = "#15171B"
PANEL = "#1B1E24"
PANEL_ALT = "#20232B"
BORDER = "#2A2E37"
TEXT = "#E7E9EE"
TEXT_DIM = "#8A90A0"
DANGER = "#FF4D4F"

STATUS_COLORS = {
    "READY": "#2F8FFF",
    "LISTENING": "#37D6C6",
    "THINKING": "#F5C542",
    "SEARCHING": "#F5C542",
    "SPEAKING": "#37D6C6",
    "ACTION": "#2F8FFF",
    "ERROR": "#FF4D4F",
}


def stylesheet(accent: str = "#2F8FFF") -> str:
    return f"""
    QWidget {{
        background-color: {BG};
        color: {TEXT};
        font-family: "Segoe UI", "Inter", sans-serif;
        font-size: 13px;
    }}

    #Sidebar {{
        background-color: {PANEL};
        border-right: 1px solid {BORDER};
    }}

    QPushButton#NavButton {{
        background-color: transparent;
        color: {TEXT_DIM};
        border: none;
        text-align: left;
        padding: 10px 16px;
        border-radius: 6px;
        font-size: 13px;
    }}
    QPushButton#NavButton:hover {{
        background-color: {PANEL_ALT};
        color: {TEXT};
    }}
    QPushButton#NavButton:checked {{
        background-color: {PANEL_ALT};
        color: {accent};
        border-left: 3px solid {accent};
    }}

    #TopBar {{
        background-color: {PANEL};
        border-bottom: 1px solid {BORDER};
    }}

    #TitleLabel {{
        font-size: 16px;
        font-weight: 600;
        letter-spacing: 2px;
    }}

    #StatusPill {{
        background-color: {PANEL_ALT};
        border: 1px solid {BORDER};
        border-radius: 12px;
        padding: 4px 12px;
    }}

    QTextEdit#Transcript, QListWidget {{
        background-color: {PANEL};
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 8px;
    }}

    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
        background-color: {PANEL_ALT};
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 6px 10px;
        color: {TEXT};
    }}
    QLineEdit:focus, QComboBox:focus {{
        border: 1px solid {accent};
    }}

    QPushButton#PrimaryButton {{
        background-color: {accent};
        color: #0A0C10;
        border: none;
        border-radius: 6px;
        padding: 8px 18px;
        font-weight: 600;
    }}
    QPushButton#PrimaryButton:hover {{
        background-color: #4FA3FF;
    }}
    QPushButton#PrimaryButton:disabled {{
        background-color: {BORDER};
        color: {TEXT_DIM};
    }}

    QPushButton#SecondaryButton {{
        background-color: transparent;
        color: {TEXT};
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 8px 16px;
    }}
    QPushButton#SecondaryButton:hover {{
        border: 1px solid {accent};
        color: {accent};
    }}

    QPushButton#StopButton {{
        background-color: {DANGER};
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 700;
        font-size: 15px;
        letter-spacing: 2px;
        padding: 12px;
    }}
    QPushButton#StopButton:hover {{
        background-color: #FF7072;
    }}

    QGroupBox {{
        border: 1px solid {BORDER};
        border-radius: 8px;
        margin-top: 14px;
        padding: 12px;
        font-weight: 600;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 4px;
        color: {TEXT_DIM};
    }}

    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
    }}
    QScrollBar::handle:vertical {{
        background: {BORDER};
        border-radius: 4px;
    }}
    """
