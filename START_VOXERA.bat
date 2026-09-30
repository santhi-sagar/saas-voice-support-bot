@echo off
setlocal
cd /d "%~dp0"
set "PYTHON_EXE=.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" (
  echo First-time setup: creating a local Python environment...
  where py >nul 2>nul
  if %errorlevel%==0 (py -3 -m venv .venv) else (python -m venv .venv)
  if errorlevel 1 (
    echo Python 3.10 or newer is required. Install Python from https://www.python.org/downloads/
    pause
    exit /b 1
  )
  echo First-time setup: installing local dependencies...
  "%PYTHON_EXE%" -m pip install -r requirements.txt
  if errorlevel 1 (
    echo Dependency installation failed. Check your internet connection and run this file again.
    pause
    exit /b 1
)
echo Starting Voxera locally at http://127.0.0.1:8765
start "" http://127.0.0.1:8765
"%PYTHON_EXE%" -m uvicorn app:app --host 127.0.0.1 --port 8765
pause
