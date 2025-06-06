@echo off
REM CryptoFinance Corpus Builder v3 - Windows Launcher
REM (Activates your preferred venv, then runs the app)

call G:\venv312\Scripts\Activate.ps1

REM Navigate to the application directory
cd /d %~dp0

REM Run the application
G:\venv312\Scripts\python.exe app/main.py

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo Application exited with an error.
    pause
)
