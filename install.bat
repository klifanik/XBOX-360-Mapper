@echo off
setlocal enabledelayedexpansion
title HID -^> Xbox 360 Mapper - Installation
cd /d "%~dp0"

echo ============================================
echo   HID -^> Xbox 360 Mapper - Installation
echo ============================================
echo.

:: --- 1. Check if Python is installed ---
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python was not found on this computer.
    echo Downloading Python 3.12 installer ^(internet connection required^)...
    set "PY_URL=https://www.python.org/ftp/python/3.12.6/python-3.12.6-amd64.exe"
    set "PY_INSTALLER=%TEMP%\python_installer.exe"

    curl -L -o "%PY_INSTALLER%" "%PY_URL%"
    if not exist "%PY_INSTALLER%" (
        echo.
        echo Failed to download the installer automatically.
        echo Please install Python manually from https://python.org/downloads/
        echo ^(make sure to check "Add python.exe to PATH"^) and run install.bat again.
        echo.
        pause
        exit /b 1
    )

    echo Installing Python ^(a UAC prompt may appear - please confirm^)...
    "%PY_INSTALLER%" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 Include_tcltk=1
    del "%PY_INSTALLER%" >nul 2>nul

    echo.
    echo Python installed. If the next step fails, close this window
    echo and run install.bat again ^(required for Windows to refresh PATH^).
    echo.
) else (
    echo Python is already installed:
    python --version
)

echo.
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Command "python" is still not found. Restart install.bat
    echo or reboot your PC and try again.
    pause
    exit /b 1
)

:: --- 2. Update pip and install required packages ---
echo Updating pip...
python -m pip install --upgrade pip

echo.
echo Installing dependencies ^(pygame, vgamepad^)...
python -m pip install pygame vgamepad
if %errorlevel% neq 0 (
    echo.
    echo Failed to install dependencies. Check your internet connection
    echo and try running install.bat again.
    pause
    exit /b 1
)

echo.
echo ============================================
echo IMPORTANT: A ViGEmBus driver is required
echo for the virtual Xbox 360 gamepad to work.
echo The vgamepad package usually installs it
echo automatically during setup ^(a separate UAC
echo prompt/installer may appear - just complete it^).
echo.
echo If the virtual gamepad fails to create after
echo launching the app, install the driver manually:
echo https://github.com/ViGEm/ViGEmBus/releases
echo ============================================
echo.
echo Installation complete! You can now launch run.bat
echo.
pause