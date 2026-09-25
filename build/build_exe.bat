@echo off
setlocal

REM ============================================================
REM Alex - Windows build script
REM
REM Run locally:
REM     build\build_exe.bat
REM
REM GitHub Actions:
REM     build\build_exe.bat
REM
REM Output:
REM     dist\Alex.exe
REM ============================================================

cd /d "%~dp0.."

echo.
echo ========================================
echo        Alex - Windows Build
echo ========================================
echo.

echo [1/6] Checking Python...

where python >nul 2>&1
if errorlevel 1 goto :NO_PYTHON

python --version
if errorlevel 1 goto :NO_PYTHON

echo.
echo [2/6] Preparing Python environment...

if defined CI goto :CI_ENV

if exist ".venv\Scripts\python.exe" goto :VENV_READY

echo Creating virtual environment...
python -m venv .venv
if errorlevel 1 goto :VENV_FAILED

:VENV_READY
echo Activating virtual environment...
call ".venv\Scripts\activate.bat"
if errorlevel 1 goto :VENV_FAILED

goto :INSTALL

:CI_ENV
echo GitHub Actions detected.
echo Using the runner Python directly.

:INSTALL
echo.
echo [3/6] Installing dependencies...

python -m pip install --upgrade pip
if errorlevel 1 goto :PIP_FAILED

if not exist "requirements.txt" goto :NO_REQUIREMENTS

python -m pip install -r requirements.txt
if errorlevel 1 goto :DEPENDENCY_FAILED

:NO_REQUIREMENTS
echo.
echo [4/6] Installing PyInstaller...

python -m pip install pyinstaller
if errorlevel 1 goto :PYINSTALLER_FAILED

echo.
echo [5/6] Preparing build folders...

if exist "build\pyinstaller_work" rmdir /s /q "build\pyinstaller_work"
if exist "dist\Alex.exe" del /f /q "dist\Alex.exe"

if not exist "dist" mkdir "dist"

echo.
echo [6/6] Building Alex.exe...
echo.

if not exist "main.py" goto :NO_MAIN

if exist "assets\icon.ico" goto :BUILD_WITH_ICON

echo No icon found.
echo Building without an application icon.
echo.

python -m PyInstaller ^
--name Alex ^
--onefile ^
--windowed ^
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

goto :CHECK_BUILD

:BUILD_WITH_ICON
echo Icon found: assets\icon.ico
echo.

python -m PyInstaller ^
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

:CHECK_BUILD

if errorlevel 1 goto :BUILD_FAILED

if not exist "dist\Alex.exe" goto :BUILD_FAILED

echo.
echo ========================================
echo          BUILD SUCCESSFUL
echo ========================================
echo.
echo Alex.exe:
echo %CD%\dist\Alex.exe
echo.

if defined CI goto :END

echo Press any key to close...
pause >nul
goto :END

:NO_PYTHON
echo.
echo ERROR: Python was not found.
echo Install Python 3.10-3.12 and make sure Python is on PATH.
echo.
if defined CI goto :END
pause
goto :END

:VENV_FAILED
echo.
echo ERROR: Could not create or activate the Python virtual environment.
echo.
if defined CI goto :END
pause
goto :END

:PIP_FAILED
echo.
echo ERROR: pip installation failed.
echo.
if defined CI goto :END
pause
goto :END

:DEPENDENCY_FAILED
echo.
echo ERROR: requirements.txt installation failed.
echo.
if defined CI goto :END
pause
goto :END

:NO_REQUIREMENTS
echo WARNING: requirements.txt was not found.
echo Continuing without project dependencies.
goto :INSTALL

:PYINSTALLER_FAILED
echo.
echo ERROR: PyInstaller installation failed.
echo.
if defined CI goto :END
pause
goto :END

:NO_MAIN
echo.
echo ERROR: main.py was not found.
echo The build expects main.py in the project root.
echo.
if defined CI goto :END
pause
goto :END

:BUILD_FAILED
echo.
echo ========================================
echo             BUILD FAILED
echo ========================================
echo.
echo PyInstaller could not create dist\Alex.exe.
echo Read the PyInstaller error above.
echo.
if defined CI goto :END
pause
goto :END

:END
endlocal
exit /b 0
