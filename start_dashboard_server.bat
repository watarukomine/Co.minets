@echo off
setlocal
cd /d "%~dp0"

echo Starting Dashboard Server...
echo Port: 8888
echo --------------------------------------------------

:: Check for python
python --version > nul 2>&1
if %errorlevel% neq 0 (
    py --version > nul 2>&1
    if %errorlevel% neq 0 (
        echo Error: Python not found.
        pause
        exit /b
    )
    set PY_CMD=py
) else (
    set PY_CMD=python
)

:: Start browser in background with 3-second delay
:: This allows the server to initialize first.
echo Preparing browser...
start /b "" cmd /c "timeout /t 3 > nul && start http://127.0.0.1:8888/index.html"

:: Start HTTP Server in foreground
echo Server is launching on http://127.0.0.1:8888
echo [IMPORTANT] DO NOT CLOSE THIS WINDOW while using the dashboard.
%PY_CMD% -m http.server 8888 --bind 127.0.0.1

if %errorlevel% neq 0 (
    echo Server failed to start.
    pause
)
