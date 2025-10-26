@echo off
REM ComfyUI HiTem3D Integration Installation Script (Windows)
REM Created by: Geekatplay Studio by Vladimir Chopine
REM Website: www.geekatplay.com
REM Get HiTem3D Credits: https://www.hitem3d.ai/?sp_source=Geekatplay

echo Installing ComfyUI HiTem3D Integration...
echo Created by Geekatplay Studio by Vladimir Chopine
echo Visit: www.geekatplay.com

REM Check if we're in the right directory
if not exist "requirements.txt" (
    echo Error: requirements.txt not found. Please run this script from the comfyui-hitem3d directory.
    pause
    exit /b 1
)

REM Find ComfyUI's embedded Python
set "PYTHON_EXE="
set "COMFYUI_ROOT=%~dp0..\..\..\"

REM Try to find Python executable in common ComfyUI locations
if exist "%COMFYUI_ROOT%python_embeded\python.exe" (
    set "PYTHON_EXE=%COMFYUI_ROOT%python_embeded\python.exe"
    echo Found embedded Python at: %PYTHON_EXE%
) else if exist "%COMFYUI_ROOT%python\python.exe" (
    set "PYTHON_EXE=%COMFYUI_ROOT%python\python.exe"
    echo Found embedded Python at: %PYTHON_EXE%
) else if exist "%COMFYUI_ROOT%..\python_embeded\python.exe" (
    set "PYTHON_EXE=%COMFYUI_ROOT%..\python_embeded\python.exe"
    echo Found embedded Python at: %PYTHON_EXE%
) else (
    REM Try system Python as fallback
    where python >nul 2>&1
    if %errorlevel% equ 0 (
        set "PYTHON_EXE=python"
        echo Using system Python
    ) else (
        echo Error: Could not find Python executable.
        echo Please ensure ComfyUI's embedded Python is available or Python is in your PATH.
        pause
        exit /b 1
    )
)

REM Install Python dependencies
echo Installing Python dependencies...
"%PYTHON_EXE%" -m pip install -r requirements.txt

if %errorlevel% equ 0 (
    echo ✅ Dependencies installed successfully!
) else (
    echo ❌ Failed to install dependencies. Please check the error messages above.
    pause
    exit /b 1
)

REM Check if config file exists
if exist "config.json" (
    echo ✅ Configuration file found.
    echo 📝 Please update config.json with your HiTem3D API credentials:
    echo    - Access Key: Your HiTem3D access key
    echo    - Secret Key: Your HiTem3D secret key
) else (
    echo ❌ Configuration file not found. Please ensure config.json exists.
)

echo.
echo 🎉 Installation complete!
echo.
echo Next steps:
echo 1. Update config.json with your API credentials
echo 2. Restart ComfyUI
echo 3. Look for HiTem3D nodes in the node menu
echo.
echo For help, see README.md or visit: www.geekatplay.com
echo Get HiTem3D credits: https://www.hitem3d.ai/?sp_source=Geekatplay
echo.
pause