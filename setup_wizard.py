#!/usr/bin/env python3
"""
HiTem3D Setup Wizard
Created by: Geekatplay Studio by Vladimir Chopine
Website: www.geekatplay.com
"""

import json
import os
import sys
import re
from pathlib import Path

def print_banner():
    """Print the setup banner"""
    print("\n" + "="*60)
    print("🎯 HiTem3D Custom Node Setup Wizard")
    print("Created by: Geekatplay Studio by Vladimir Chopine")
    print("Website: www.geekatplay.com")
    print("="*60)

def validate_api_key(key, key_type):
    """Validate API key format"""
    if key_type == "access":
        pattern = r'^ak_[a-f0-9]{32}$'
        if not re.match(pattern, key):
            print(f"❌ Invalid access key format. Should be: ak_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
            return False
    elif key_type == "secret":
        pattern = r'^sk_[a-f0-9]{32}$'
        if not re.match(pattern, key):
            print(f"❌ Invalid secret key format. Should be: sk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
            return False
    return True

def get_api_credentials():
    """Get API credentials from user"""
    print("\n📋 Step 1: API Credentials")
    print("-" * 30)
    print("🔗 First, get your API keys from:")
    print("   https://www.hitem3d.ai/?sp_source=Geekatplay")
    print("   → Register/Login → API/Developer section")
    print("")
    
    # Get Access Key
    while True:
        access_key = input("🔑 Enter your Access Key (ak_...): ").strip()
        if not access_key:
            print("❌ Access key cannot be empty!")
            continue
        if validate_api_key(access_key, "access"):
            break
        print("💡 Example: ak_1234567890abcdef1234567890abcdef")
    
    # Get Secret Key
    while True:
        secret_key = input("🔐 Enter your Secret Key (sk_...): ").strip()
        if not secret_key:
            print("❌ Secret key cannot be empty!")
            continue
        if validate_api_key(secret_key, "secret"):
            break
        print("💡 Example: sk_1234567890abcdef1234567890abcdef")
    
    return access_key, secret_key

def get_advanced_settings():
    """Get advanced configuration settings"""
    print("\n⚙️  Step 2: Advanced Settings (Optional)")
    print("-" * 40)
    
    # Default model
    print("📦 Available models:")
    print("   1. hitem3dv2.0 (new)")
    print("   2. hitem3dv1.5 (recommended)")
    print("   3. hitem3dv1.0")
    model_choice = input("Choose model (1-3, default=2): ").strip()
    
    if model_choice == "1":
        model = "hitem3dv2.0"
    elif model_choice == "3":
        model = "hitem3dv1.0"
    else:
        model = "hitem3dv1.5"
    
    # Default resolution
    print("\n📐 Default resolution:")
    print("   1. 512 (fastest, lowest quality)")
    print("   2. 1024 (balanced, recommended)")
    print("   3. 1536 (slowest, highest quality)")
    res_choice = input("Choose resolution (1-3, default=2): ").strip()
    resolution_map = {"1": 512, "2": 1024, "3": 1536}
    resolution = resolution_map.get(res_choice, 1024)
    
    # Timeout
    timeout_input = input(f"\n⏱️  Timeout in seconds (default=300): ").strip()
    try:
        timeout = int(timeout_input) if timeout_input else 300
        if timeout < 60:
            timeout = 300
            print("⚠️  Minimum timeout is 60 seconds, using default 300")
    except ValueError:
        timeout = 300
        print("⚠️  Invalid timeout, using default 300 seconds")
    
    return model, resolution, timeout

def save_config(access_key, secret_key, model, resolution, timeout):
    """Save configuration to config.json"""
    config = {
        "hitem3d": {
            "access_key": access_key,
            "secret_key": secret_key,
            "api_base_url": "https://api.hitem3d.ai",
            "default_model": model,
            "default_resolution": resolution,
            "default_format": 2,
            "default_face_count": 1000000,
            "timeout": timeout
        }
    }
    
    config_path = Path(__file__).parent / "config.json"
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
        print(f"\n✅ Configuration saved to: {config_path}")
        return True
    except Exception as e:
        print(f"\n❌ Failed to save configuration: {e}")
        return False

def test_api_connection(access_key, secret_key):
    """Test API connection"""
    print("\n🧪 Step 3: Testing API Connection")
    print("-" * 35)
    
    try:
        # Import the HiTem3D client
        sys.path.append(str(Path(__file__).parent))
        from hitem3d_client import HiTem3DAPIClient
        
        # Test connection
        print("🔄 Testing API connection...")
        client = HiTem3DAPIClient(access_key, secret_key)
        
        # Try to get account info/balance
        print("🔄 Checking account status...")
        # Note: This would need to be implemented in the actual API client
        # For now, just test token generation
        token = client.get_access_token()
        if token:
            print("✅ API connection successful!")
            print("✅ Access token obtained!")
            return True
        else:
            print("❌ Failed to obtain access token")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to import HiTem3D client: {e}")
        print("💡 Make sure dependencies are installed: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ API test failed: {e}")
        print("💡 Please check your API keys and internet connection")
        return False

def show_next_steps():
    """Show next steps after setup"""
    print("\n🎉 Setup Complete!")
    print("=" * 50)
    print("📁 Next steps:")
    print("   1. Restart ComfyUI")
    print("   2. Look for 'HiTem3D' nodes in the node menu")
    print("   3. Try the example workflows in ./examples/")
    print("")
    print("💰 Add credits to your account:")
    print("   https://www.hitem3d.ai/?sp_source=Geekatplay")
    print("")
    print("🆘 Need help?")
    print("   • Check TROUBLESHOOTING.md")
    print("   • Visit: www.geekatplay.com")
    print("   • YouTube: @geekatplay")
    print("=" * 50)

def main():
    """Main setup wizard"""
    try:
        print_banner()
        
        # Step 1: Get API credentials
        access_key, secret_key = get_api_credentials()
        
        # Step 2: Get advanced settings
        model, resolution, timeout = get_advanced_settings()
        
        # Save configuration
        if not save_config(access_key, secret_key, model, resolution, timeout):
            print("\n❌ Setup failed!")
            return 1
        
        # Step 3: Test API connection
        connection_ok = test_api_connection(access_key, secret_key)
        
        # Show completion message
        show_next_steps()
        
        if not connection_ok:
            print("\n⚠️  Note: API test failed, but configuration was saved.")
            print("   Please check your keys and internet connection.")
            return 1
        
        print("\n🎯 Setup completed successfully!")
        return 0
        
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    input("\nPress Enter to exit...")
    sys.exit(exit_code)