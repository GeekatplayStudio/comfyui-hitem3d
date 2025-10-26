@echo off
REM ComfyUI HiTem3D Integration Installation Script (Windows) - Direct Path Version
REM Created by: Geekatplay Studio by Vladimir Chopine
REM Website: www.geekatplay.com
REM Get HiTem3D Credits: https://www.hitem3d.ai/?sp_source=Geekatplay

echo Installing ComfyUI HiTem3D Integration...
echo Created by Geekatplay Studio by Vladimir Chopine

REM Set the path to your ComfyUI embedded Python (adjust if needed)
set "PYTHON_EXE=%~dp0..\..\..\..\python_embeded\python.exe"

REM Alternative paths if the above doesn't work:
REM set "PYTHON_EXE=%~dp0..\..\..\..\python\python.exe"

REM Check if Python executable exists
if not exist "%PYTHON_EXE%" (
    echo Error: Python executable not found at %PYTHON_EXE%
    echo Please check your ComfyUI installation path.
    echo.
    echo Alternative paths to try:
    echo - ../../python/python.exe
    echo - ../../python_embeded/python.exe
    echo.
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "requirements.txt" (
    echo Error: requirements.txt not found. Please run this script from the comfyui-hitem3d directory.
    pause
    exit /b 1
)

echo Found Python at: %PYTHON_EXE%
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