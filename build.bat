@echo off
setlocal

:: -------- Configuration --------
:: 1 = dev build (console visible)
:: 0 = release build (no console)
set DEV_MODE=0
set APP_NAME=RankedDSTProxy

:: -------- App name suffix --------
if "%DEV_MODE%"=="1" (
    set APP_NAME=%APP_NAME%Dev
)
set ENTRY_POINT=RankedDST\__main__.py
set VENV_PYTHON=venv\Scripts\python.exe

:: -------- Checks --------
if not exist "%VENV_PYTHON%" (
    echo [ERROR] Virtual environment not found.
    echo Run: python -m venv venv
    pause
    exit /b 1
)

echo [INFO] Using Python: %VENV_PYTHON%

:: -------- Clean old builds --------
if exist build rmdir /s /q build
:: if exist dist rmdir /s /q dist

:: -------- Build flags --------
set PYI_FLAGS=--onefile --name %APP_NAME%

if "%DEV_MODE%"=="0" (
    echo [INFO] Release build (no console)
    set PYI_FLAGS=%PYI_FLAGS% --noconsole
) else (
    echo [INFO] Dev build (console enabled)
)

:: -------- Add UI resources --------
set ICON_PATH=RankedDST\ui\resources\icons\calibrated_perceiver.ico
set PYI_FLAGS=%PYI_FLAGS% ^
 --add-data "RankedDST\ui\resources;RankedDST/ui/resources" --icon "%ICON_PATH%"

:: -------- Build --------
echo [INFO] Building %APP_NAME%...
"%VENV_PYTHON%" -m PyInstaller ^
    %PYI_FLAGS% ^
    %ENTRY_POINT%

if errorlevel 1 (
    echo [ERROR] Build failed.
    pause
    exit /b 1
)

echo [SUCCESS] Build complete.
echo Output: dist\%APP_NAME%.exe
pause
