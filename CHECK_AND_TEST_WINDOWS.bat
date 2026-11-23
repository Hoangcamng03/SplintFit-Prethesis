@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run START_WINDOWS.bat first to create the Python environment.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m pip check
if errorlevel 1 goto fail
".venv\Scripts\python.exe" -m unittest discover -s tests -v
if errorlevel 1 goto fail
echo Tests passed. Windows 3D interaction and Fusion conversion still need manual testing.
pause
exit /b 0
:fail
echo Check failed. Copy the error above.
pause
exit /b 1
