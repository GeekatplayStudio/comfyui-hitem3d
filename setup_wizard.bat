@echo off
echo ===============================================
echo HiTem3D Setup Wizard
echo Created by: Geekatplay Studio by Vladimir Chopine
echo ===============================================
echo.

:: Find Python executable
set PYTHON_CMD=
if exist "..\..\python_embeded\python.exe" (
    set PYTHON_CMD=..\..\python_embeded\python.exe
) else if exist "..\..\python\python.exe" (
    set PYTHON_CMD=..\..\python\python.exe
) else if exist "..\..\..\python_embeded\python.exe" (
    set PYTHON_CMD=..\..\..\python_embeded\python.exe
) else (
    echo Error: Could not find ComfyUI Python executable
    echo Please run setup_wizard.py manually with your Python path
    echo Example: python setup_wizard.py
    pause
    exit /b 1
)

echo Found Python: %PYTHON_CMD%
echo.

:: Run setup wizard
"%PYTHON_CMD%" setup_wizard.py

echo.
echo Setup wizard completed!
pause