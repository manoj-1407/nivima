@echo off
setlocal enabledelayedexpansion

echo ==================================================================
echo    Nivima Automated Windows Bootstrap for Fresh Gaming Laptops
echo ==================================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\setup_fresh_windows.ps1"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ==================================================================
    echo    Setup Completed Successfully!
    echo ==================================================================
) else (
    echo.
    echo [ERROR] Setup encountered an issue. Please review the output above.
)

pause
