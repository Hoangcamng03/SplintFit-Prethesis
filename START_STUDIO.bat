@echo off
title SplintFit Studio
set "PY=C:\Users\USER\AppData\Local\Programs\Python\Python312\python.exe"
if not exist "%PY%" set "PY=python"
set "URL=http://127.0.0.1:8765"

echo Dang khoi dong SplintFit Studio (Che do cua so ung dung doc lap)...
start "" /b "%PY%" "%~dp0backend\server.py"
timeout /t 2 /nobreak >nul

rem Mo dang cua so Desktop App doc lap (khong thanh dia chi, khong tab trinh duyet)
if exist "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" (
    start "" "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" --app=%URL% --window-size=1440,900
    exit /b
)
if exist "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" (
    start "" "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" --app=%URL% --window-size=1440,900
    exit /b
)
if exist "%ProgramFiles%\BraveSoftware\Brave-Browser\Application\brave.exe" (
    start "" "%ProgramFiles%\BraveSoftware\Brave-Browser\Application\brave.exe" --app=%URL% --window-size=1440,900
    exit /b
)
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
    start "" "%ProgramFiles%\Google\Chrome\Application\chrome.exe" --app=%URL% --window-size=1440,900
    exit /b
)

start "" %URL%
