@echo off
title SplintFit Studio - 3D Splint & Fusion 360 Form Designer
set "PY=C:\Users\USER\AppData\Local\Programs\Python\Python312\python.exe"
if not exist "%PY%" set "PY=python"
echo Dang khoi dong SplintFit Studio tai http://127.0.0.1:8765 ...
start "" http://127.0.0.1:8765
"%PY%" "%~dp0backend\server.py"
pause
