@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo First run: creating Python environment...
  py -3.12 -m venv .venv 2>nul
  if errorlevel 1 (
    py -3.11 -m venv .venv 2>nul
    if errorlevel 1 (
      python -m venv .venv
      if errorlevel 1 goto fail
    )
  )
)
if not exist ".venv\splintfit_cast_v40_installed.flag" (
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 goto fail
  echo installed>".venv\splintfit_cast_v40_installed.flag"
)
".venv\Scripts\python.exe" app.py
if errorlevel 1 goto fail
exit /b 0
:fail
echo Could not start. Read BAT_DAU_O_DAY.md. Python 3.11 or 3.12 and internet are needed for first setup.
pause
exit /b 1
