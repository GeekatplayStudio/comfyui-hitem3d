#!/bin/bash

# ComfyUI HiTem3D Integration Installation Script
# Created by: Geekatplay Studio by Vladimir Chopine
# Website: www.geekatplay.com
# Get HiTem3D Credits: https://www.hitem3d.ai/?sp_source=Geekatplay

echo "Installing ComfyUI HiTem3D Integration..."
echo "Created by Geekatplay Studio by Vladimir Chopine"

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "Error: requirements.txt not found. Please run this script from the comfyui-hitem3d directory."
    exit 1
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully!"
else
    echo "❌ Failed to install dependencies. Please check the error messages above."
    exit 1
fi

# Check if config file exists
if [ -f "config.json" ]; then
    echo "✅ Configuration file found."
    echo "📝 Please update config.json with your HiTem3D API credentials:"
    echo "   - Access Key: Your HiTem3D access key"
    echo "   - Secret Key: Your HiTem3D secret key"
else
    echo "❌ Configuration file not found. Please ensure config.json exists."
fi

echo ""
echo "🎉 Installation complete!"
echo ""
echo "Next steps:"
echo "1. Update config.json with your API credentials"
echo "2. Restart ComfyUI"
echo "3. Look for HiTem3D nodes in the node menu"
echo ""
echo "For help, see README.md or visit: www.geekatplay.com"
echo "Get HiTem3D credits: https://www.hitem3d.ai/?sp_source=Geekatplay"