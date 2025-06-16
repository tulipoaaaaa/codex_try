@echo off
REM Crypto Corpus Builder v3 - Windows Launcher
REM (Activates your preferred venv, then runs the app)

REM Change to the main project directory
cd /d G:\codex\codex_try

set PYTHONPATH=G:\codex\codex_try
set QT_DEBUG_PLUGINS=1
set QT_QPA_PLATFORM=windows
set ENABLE_QT=1
set QT_PLUGIN_PATH=%VIRTUAL_ENV%\Lib\site-packages\PySide6\plugins
set QT_LOGGING_RULES="*.debug=true;qt.qpa.*=true"

REM Run the application
G:\venvui\Scripts\python.exe CorpusBuilderApp/app/main.py

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo Application exited with an error.
    pause
)
