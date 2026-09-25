@echo off
title KameraPh Studio Suite
echo ===================================================
echo     Launching KameraPh Studio Suite (Port 8000)...
echo ===================================================
echo.
start http://127.0.0.1:8000
python -m uvicorn api_server:app --host 127.0.0.1 --port 8000
pause
