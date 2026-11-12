@echo off
title RUTH - Private AI Assistant
set OLLAMA="C:\Users\hp\AppData\Local\Programs\Ollama\ollama.exe"
set RUTH_DIR=d:\Ruth

echo.
echo  ============================================
echo    RUTH - Private AI Business Assistant
echo    100%% Local - No External APIs
echo  ============================================
echo.

REM Start Ollama server in a separate window
echo [1/3] Starting Ollama AI engine...
start "Ollama AI Server" /MIN %OLLAMA% serve
timeout /t 6 /nobreak >nul

REM Check if phi3:mini model is downloaded
echo [2/3] Checking AI model...
%OLLAMA% list 2>nul | findstr "phi3" >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo     Downloading phi3:mini model - FIRST TIME ONLY (~2.3GB)
    echo     This will take a few minutes depending on your internet...
    echo.
    %OLLAMA% pull phi3:mini
    if %errorlevel% neq 0 (
        echo ERROR: Could not download model. Check internet connection.
        pause
        exit /b 1
    )
    echo     Model downloaded successfully!
) else (
    echo     AI model ready!
)

echo [3/3] Starting Ruth...
echo.
cd /d %RUTH_DIR%

echo  ============================================
echo   Choose Mode:
echo   [1] Text Mode (type commands - test first)
echo   [2] Voice Mode (speak to Ruth)
echo   [3] Training Mode (teach Ruth about your business)
echo  ============================================
echo.
set /p mode="  Enter choice (1/2/3): "

if "%mode%"=="1" python run_ruth.py --text
if "%mode%"=="2" python run_ruth.py
if "%mode%"=="3" python run_ruth.py --train

pause
