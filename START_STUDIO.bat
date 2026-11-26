@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -3.12 -m venv .venv
  if errorlevel 1 goto fail
)
echo Checking Python dependencies. Internet is needed on first setup.
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto fail
".venv\Scripts\python.exe" launch_studio.py
if errorlevel 1 goto fail
exit /b 0
:fail
echo Studio could not start. Use Python 3.12 64-bit and read the error above.
pause
exit /b 1
