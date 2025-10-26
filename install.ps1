# ComfyUI HiTem3D Integration Installation Script (PowerShell)
# Created by: Geekatplay Studio by Vladimir Chopine
# Website: www.geekatplay.com
# Get HiTem3D Credits: https://www.hitem3d.ai/?sp_source=Geekatplay

Write-Host "Installing ComfyUI HiTem3D Integration..." -ForegroundColor Green
Write-Host "Created by Geekatplay Studio by Vladimir Chopine" -ForegroundColor Cyan

# Set the path to your ComfyUI embedded Python (adjust if needed)
$PythonExe = Join-Path $PSScriptRoot "..\..\..\..\python_embeded\python.exe"

# Check if Python executable exists
if (-not (Test-Path $PythonExe)) {
    Write-Host "Error: Python executable not found at $PythonExe" -ForegroundColor Red
    Write-Host "Please check your ComfyUI installation path." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Alternative paths to try:" -ForegroundColor Yellow
    Write-Host "- ../../python/python.exe"
    Write-Host "- ../../python_embeded/python.exe"
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if we're in the right directory
if (-not (Test-Path "requirements.txt")) {
    Write-Host "Error: requirements.txt not found. Please run this script from the comfyui-hitem3d directory." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Found Python at: $PythonExe" -ForegroundColor Green
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow

# Install dependencies
try {
    & $PythonExe -m pip install -r requirements.txt
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Dependencies installed successfully!" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to install dependencies. Please check the error messages above." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
} catch {
    Write-Host "❌ Failed to install dependencies: $($_.Exception.Message)" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if config file exists
if (Test-Path "config.json") {
    Write-Host "✅ Configuration file found." -ForegroundColor Green
    Write-Host "📝 Please update config.json with your HiTem3D API credentials:" -ForegroundColor Yellow
    Write-Host "   - Access Key: Your HiTem3D access key"
    Write-Host "   - Secret Key: Your HiTem3D secret key"
} else {
    Write-Host "❌ Configuration file not found. Please ensure config.json exists." -ForegroundColor Red
}

Write-Host ""
Write-Host "🎉 Installation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Update config.json with your API credentials"
Write-Host "2. Restart ComfyUI"
Write-Host "3. Look for HiTem3D nodes in the node menu"
Write-Host ""
Write-Host "For help, see README.md or visit: www.geekatplay.com" -ForegroundColor Cyan
Write-Host "Get HiTem3D credits: https://www.hitem3d.ai/?sp_source=Geekatplay" -ForegroundColor Yellow
Write-Host ""
Read-Host "Press Enter to exit"