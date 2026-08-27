@echo off
cd /d "%~dp0"

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python не найден. Сначала запустите install.bat
    pause
    exit /b 1
)

python hid_mapper.py
if errorlevel 1 (
    echo.
    echo Программа завершилась с ошибкой ^(текст выше^).
    echo Если написано что-то про модуль pygame/vgamepad — запустите install.bat заново.
    pause
)
