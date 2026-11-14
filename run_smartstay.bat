@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" app.py
    exit /b %errorlevel%
)

if exist ".venv\bin\python.exe" (
    ".venv\bin\python.exe" app.py
    exit /b %errorlevel%
)

py app.py
