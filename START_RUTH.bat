@echo off
echo.
echo  =============================================
echo    RUTH - Private AI Assistant Launcher
echo    100%% Local - No External APIs
echo  =============================================
echo.
echo  [1] Start Ruth (Voice Mode)
echo  [2] Start Ruth (Text Mode - no mic needed)
echo  [3] Training Mode (teach Ruth about your business)
echo  [4] Setup AI Model (run ONCE after Ollama install)
echo  [5] Install Dependencies
echo  [6] Exit
echo.
set /p choice="  Choose (1-6): "

if "%choice%"=="1" (
    echo.
    echo Starting Ruth in Voice Mode...
    echo NOTE: Make sure Ollama is running (ollama serve)
    python run_ruth.py
)
if "%choice%"=="2" (
    echo.
    echo Starting Ruth in Text Mode...
    echo NOTE: Make sure Ollama is running (ollama serve)
    python run_ruth.py --text
)
if "%choice%"=="3" (
    echo.
    echo Starting Training Mode...
    python run_ruth.py --train
)
if "%choice%"=="4" (
    echo.
    echo Setting up AI Model...
    python setup_model.py
    pause
)
if "%choice%"=="5" (
    echo.
    echo Installing dependencies...
    python setup.py
    pause
)
if "%choice%"=="6" exit
pause
