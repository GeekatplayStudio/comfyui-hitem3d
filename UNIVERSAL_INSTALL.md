# Universal Installation Guide

**Created by:** Geekatplay Studio by Vladimir Chopine  
**Get HiTem3D Credits:** [https://www.hitem3d.ai/?sp_source=Geekatplay](https://www.hitem3d.ai/?sp_source=Geekatplay)

## Installation for Any ComfyUI Setup

This guide works for any ComfyUI installation, regardless of location or operating system.

### Method 1: Automatic Installation (Recommended)

1. **Navigate to the custom node directory:**
   ```powershell
   cd "path/to/your/ComfyUI/custom_nodes/comfyui-hitem3d"
   ```

2. **Run the appropriate installer:**
   - **Windows:** `install_direct.bat` or `install.ps1`
   - **Linux/Mac:** `install.sh`

### Method 2: Manual Installation

1. **Find your ComfyUI Python executable:**
   - Look for: `ComfyUI/python_embeded/python.exe` (Windows)
   - Or: `ComfyUI/python/python.exe`
   - Linux/Mac: `ComfyUI/python_embeded/python` or `ComfyUI/python/python`

2. **Install dependencies:**
   ```bash
   # Replace [PYTHON_PATH] with your actual Python path
   [PYTHON_PATH] -m pip install -r requirements.txt
   ```

### Common ComfyUI Structures

**Portable Installation:**
```
ComfyUI/
├── python_embeded/
│   └── python.exe
├── ComfyUI/
│   └── custom_nodes/
│       └── comfyui-hitem3d/
└── models/
```

**Standard Installation:**
```
ComfyUI/
├── python/
│   └── python.exe
├── custom_nodes/
│   └── comfyui-hitem3d/
└── models/
```

**Development Installation:**
```
ComfyUI/
├── venv/
│   └── bin/python (Linux/Mac)
│   └── Scripts/python.exe (Windows)
└── custom_nodes/
    └── comfyui-hitem3d/
```

### Finding Your Python Path

**Windows PowerShell:**
```powershell
# From ComfyUI root directory
Get-ChildItem -Recurse -Name "python.exe" | Select-Object -First 3
```

**Linux/Mac Terminal:**
```bash
# From ComfyUI root directory
find . -name "python" -type f | head -3
```

### Verification

After installation, test the setup:
```powershell
# Navigate to the custom node directory
cd "ComfyUI/custom_nodes/comfyui-hitem3d"

# Run the balance checker (replace [PYTHON_PATH] with your path)
[PYTHON_PATH] check_balance.py
```

### Troubleshooting

1. **Python not found:** Check the file structure above and adjust paths
2. **Permission errors:** Run as administrator (Windows) or use `sudo` (Linux/Mac)
3. **Module errors:** Ensure you're using ComfyUI's Python, not system Python

### File Paths Reference

All paths in this project use relative references:
- **Output directory:** `ComfyUI/output/hitem3d/` (default)
- **Input directory:** `ComfyUI/input/`
- **Custom nodes:** `ComfyUI/custom_nodes/comfyui-hitem3d/`
- **Python executable:** `../../python_embeded/python.exe` (relative to custom node)

This ensures the custom node works regardless of where ComfyUI is installed!