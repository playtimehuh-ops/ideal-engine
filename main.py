"""
Alex - a voice-first desktop AI assistant.

Run with:  python main.py
Build:     build\\build_exe.bat   (on Windows)
"""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from config import settings as settings_module

if getattr(sys, "frozen", False):
    # Running as a PyInstaller-built Alex.exe: bundled files are unpacked
    # into a temp folder pointed to by sys._MEIPASS, not next to this file.
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).parent

ASSETS_DIR = BASE_DIR / "assets"


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Alex")

    icon_path = ASSETS_DIR / "icon.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    settings = settings_module.get_settings()

    if not settings.get("first_run_complete"):
        from voice.text_to_speech import TextToSpeech
        from ui.first_run_dialog import FirstRunDialog

        temp_tts = TextToSpeech()
        dialog = FirstRunDialog(tts_for_voice_list=temp_tts)
        dialog.exec()
        # Whether or not they completed the download, don't nag on every launch.
        s = settings_module.get_settings()
        s["first_run_complete"] = True
        settings_module.save_settings(s)

    from ui.main_window import MainWindow
    window = MainWindow()

    start_minimized = settings_module.get_settings()["startup"]["start_minimized"]
    if start_minimized:
        window.showMinimized()
    else:
        window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
