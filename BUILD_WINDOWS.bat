@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -3.12 -m venv .venv 2>nul
  if errorlevel 1 (
    py -3.11 -m venv .venv 2>nul
    if errorlevel 1 (
      python -m venv .venv
      if errorlevel 1 goto fail
    )
  )
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt "pyinstaller>=6.14,<7"
if errorlevel 1 goto fail
".venv\Scripts\python.exe" -m unittest discover -s tests -v
if errorlevel 1 goto fail
".venv\Scripts\python.exe" build_windows.py
if errorlevel 1 goto fail
echo Output: dist\SplintFit\SplintFit.exe
echo Distribute the entire dist\SplintFit folder, not only the exe file.
pause
exit /b 0
:fail
echo Build failed. Keep this window open and copy the error.
pause
exit /b 1
