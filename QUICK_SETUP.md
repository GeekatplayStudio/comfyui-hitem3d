# 🚀 Quick Setup Guide

**Created by:** Geekatplay Studio by Vladimir Chopine  
**Website:** [www.geekatplay.com](https://www.geekatplay.com)

## 🎯 First Time Setup (Required)

**⚠️ IMPORTANT: This package requires your personal API keys from HiTem3D!**

### Option 1: Setup Wizard (Recommended)

**Windows:**
```cmd
# Navigate to the custom node directory
cd "ComfyUI/custom_nodes/comfyui-hitem3d"

# Run the setup wizard
setup_wizard.bat
```

**Linux/Mac:**
```bash
# Navigate to the custom node directory
cd "ComfyUI/custom_nodes/comfyui-hitem3d"

# Run the setup wizard
python setup_wizard.py
```

### Option 2: Manual Configuration

1. **Get your API keys:**
   - Visit: [https://www.hitem3d.ai/?sp_source=Geekatplay](https://www.hitem3d.ai/?sp_source=Geekatplay)
   - Register/Login → API/Developer section
   - Copy your Access Key and Secret Key

2. **Edit config.json:**
   ```json
   {
       "hitem3d": {
           "access_key": "ak_your_access_key_here",
           "secret_key": "sk_your_secret_key_here",
           ...
       }
   }
   ```

### Option 3: Use ComfyUI Node

1. Load ComfyUI
2. Find `HiTem3DConfigNode` in the node menu
3. Enter your API keys directly in the node
4. This will automatically save the configuration

## ✅ Verify Setup

Test your configuration:
```cmd
# Windows
check_balance.bat

# Linux/Mac  
python check_balance.py
```

## 💰 Add Credits

**You need credits in your HiTem3D account to generate 3D models:**
- Visit: [https://www.hitem3d.ai/?sp_source=Geekatplay](https://www.hitem3d.ai/?sp_source=Geekatplay)
- Log into your account
- Purchase a resource package

## 🎮 Try It Out

1. **Restart ComfyUI** after setup
2. **Load example workflow:** `examples/hitem3d_simple_workflow.json`
3. **Add an image** to the Load Image node
4. **Click "Queue Prompt"**

## 🆘 Need Help?

- **Documentation:** `README.md`
- **Troubleshooting:** `TROUBLESHOOTING.md`  
- **Website:** [www.geekatplay.com](https://www.geekatplay.com)
- **YouTube:** [@geekatplay](https://www.youtube.com/@geekatplay)

---

**Get HiTem3D Credits:** [https://www.hitem3d.ai/?sp_source=Geekatplay](https://www.hitem3d.ai/?sp_source=Geekatplay)