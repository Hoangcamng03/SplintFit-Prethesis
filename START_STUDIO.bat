@echo off
title SplintFit Studio Desktop
set "PYW=C:\Users\USER\AppData\Local\Programs\Python\Python312\pythonw.exe"
set "PY=C:\Users\USER\AppData\Local\Programs\Python\Python312\python.exe"
if exist "%PYW%" (
    start "" "%PYW%" "%~dp0desktop\main_window.py"
    exit /b
)
if exist "%PY%" (
    "%PY%" "%~dp0desktop\main_window.py"
    exit /b
)
python "%~dp0desktop\main_window.py"
