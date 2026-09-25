@echo off
setlocal enabledelayedexpansion

REM ============================================================
REM  Alex - Windows build script
REM
REM  Local use:      build\build_exe.bat
REM  CI use:          runs the same way, but GitHub Actions sets
REM                    the CI environment variable, which this
REM                    script uses to skip the interactive parts
REM                    (creating/activating a venv, and "pause").
REM
REM  Produces: dist\Alex.exe
REM ============================================================

cd /d "%~dp0\.."

echo.
echo === Alex build: checking Python ===
where python >nul 2>nul
if errorlevel 1 (
    echo Python was not found on PATH. Install Python 3.10-3.12 from python.org
    echo and make sure "Add python.exe to PATH" is checked during install.
    if not defined CI pause
    exit /b 1
)

if defined CI (
    echo.
    echo === Running in CI: using the runner's Python directly, no venv ===
) else (
    echo.
    echo === Creating virtual environment (.venv) if needed ===
    if not exist ".venv" (
        python -m venv .venv
    )
    call ".venv\Scripts\activate.bat"
    if errorlevel 1 (
        echo Failed to activate the virtual environment.
        pause
        exit /b 1
    )
)

echo.
echo === Installing dependencies (this can take a few minutes the first time) ===
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo Dependency installation failed. See the errors above.
    if not defined CI pause
    exit /b 1
)

echo.
echo === Building Alex.exe with PyInstaller ===
if exist "build\pyinstaller_work" rmdir /s /q "build\pyinstaller_work"
if exist "dist\Alex.exe" del /f /q "dist\Alex.exe"

pyinstaller ^
    --name Alex ^
    --onefile ^
    --windowed ^
    --icon "assets\icon.ico" ^
    --add-data "assets;assets" ^
    --hidden-import vosk ^
    --hidden-import sounddevice ^
    --hidden-import pyttsx3.drivers ^
    --hidden-import pyttsx3.drivers.sapi5 ^
    --hidden-import keyring.backends.Windows ^
    --hidden-import pyautogui ^
    --workpath "build\pyinstaller_work" ^
    --specpath "build" ^
    main.py

if not exist "dist\Alex.exe" (
    echo.
    echo Build failed - dist\Alex.exe was not created. Check the PyInstaller
    echo output above for the actual error.
    if not defined CI pause
    exit /b 1
)

echo.
echo ============================================================
echo  Build complete:  dist\Alex.exe
echo.
echo  First launch will ask for your OpenRouter API key and will
echo  download a ~40MB offline speech-recognition model once.
echo ============================================================
if not defined CI pause
