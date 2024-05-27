@echo off
cls

echo *****************************
echo *        Main Menu          *
echo *****************************
echo.
echo 1. Start BOT 
echo 2. Exit
echo.

choice /c 12 /n /m "Choose an option: "

if errorlevel 2 (
    echo Exiting Menu...
    exit /b
) else (
    echo Injecting Script...
    start python beta1.py
)

echo.
echo Type "stop" to kill the BOT.
echo.

:checkStop
set /p stop=
if "%stop%"=="stop" (
    echo Stopping script...
    taskkill /im python.exe /f >nul 2>&1
    echo BOT stopped.
    exit /b
) else (
    goto checkStop
)
