"""
HiTem3D Account Balance Checker
Simple utility to check your account status and credits

Created by: Geekatplay Studio by Vladimir Chopine
Website: www.geekatplay.com
Patreon: https://www.patreon.com/c/geekatplay
YouTube: @geekatplay and @geekatplay-ru

Get HiTem3D credits with referral code: https://www.hitem3d.ai/?sp_source=Geekatplay
"""

import sys
import json
from pathlib import Path

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

def check_configuration():
    """Check if configuration is set up properly"""
    config_path = current_dir / "config.json"
    
    if not config_path.exists():
        print("❌ Configuration file not found!")
        print(f"Expected: {config_path}")
        print("💡 Run setup_wizard.py to configure your API keys")
        return False, None
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        hitem3d_config = config.get('hitem3d', {})
        access_key = hitem3d_config.get('access_key', '')
        secret_key = hitem3d_config.get('secret_key', '')
        
        # Check if keys are placeholders
        if access_key == 'YOUR_ACCESS_KEY_HERE' or not access_key.startswith('ak_'):
            print("❌ Access key not configured!")
            print("💡 Run setup_wizard.py to add your personal API keys")
            print("🔗 Get keys from: https://www.hitem3d.ai/?sp_source=Geekatplay")
            return False, None
        
        if secret_key == 'YOUR_SECRET_KEY_HERE' or not secret_key.startswith('sk_'):
            print("❌ Secret key not configured!")
            print("💡 Run setup_wizard.py to add your personal API keys")
            print("🔗 Get keys from: https://www.hitem3d.ai/?sp_source=Geekatplay")
            return False, None
        
        return True, hitem3d_config
        
    except Exception as e:
        print(f"❌ Error reading configuration: {e}")
        return False, None

def check_account_status():
    """Check HiTem3D account status and balance"""
    print("🔍 Checking HiTem3D configuration...")
    
    # First check configuration
    config_ok, config = check_configuration()
    if not config_ok:
        return False
    
    print("✅ Configuration file found and validated")
    
    try:
        from hitem3d_client import HiTem3DAPIClient
        
        print("🔄 Testing API connection...")
        
        # Create client
        client = HiTem3DAPIClient(config['access_key'], config['secret_key'])
        
        # Try to get a token (this validates credentials)
        token = client.get_access_token()
        
        if token:
            print("✅ API credentials are valid!")
            print("🔑 Access token obtained successfully")
            print()
            print("ℹ️  Account Information:")
            print(f"   • API Base URL: {client.base_url}")
            print(f"   • Access Key: {config['access_key'][:10]}...")
            print(f"   • Token Status: Active")
            print()
            print("💡 Note: This check validates your credentials but doesn't show balance.")
            print("   Balance information is only available through the generation API.")
            print()
            print("📋 Next Steps:")
            print("   1. If you get 'Insufficient balance' errors:")
            print("      - Visit: https://www.hitem3d.ai/?sp_source=Geekatplay")
            print("      - Log into your account")
            print("      - Purchase additional credits")
            print("   2. Try generating a 3D model with the example workflows")
            
            return True
        else:
            print("❌ Failed to obtain access token")
            return False
            
    except ImportError:
        print("❌ HiTem3D client not found")
        print("💡 Install dependencies: pip install -r requirements.txt")
        return False
    except Exception as e:
        error_msg = str(e)
        
        if "Invalid credentials" in error_msg or "client credentials are invalid" in error_msg:
            print("❌ INVALID CREDENTIALS")
            print("   Your Access Key or Secret Key is incorrect.")
            print("   Please check your configuration or run setup_wizard.py")
        elif "余额不足" in error_msg:
            print("⚠️  INSUFFICIENT BALANCE")
            print("   Your account has no credits remaining.")
            print("   Please add credits at: https://www.hitem3d.ai/?sp_source=Geekatplay")
        else:
            print(f"❌ Error: {error_msg}")
        
        return False

if __name__ == "__main__":
    print("HiTem3D Account Status Checker")
    print("=" * 40)
    print()
    
    success = check_account_status()
    
    if not success:
        print()
        print("🔧 Troubleshooting:")
        print("   • Check your internet connection")
        print("   • Verify API credentials in config.json")
        print("   • Get credits: https://www.hitem3d.ai/?sp_source=Geekatplay")
        print("   • Contact HiTem3D support: apicontact@hitem3d.ai")
        print("   • Visit Geekatplay: www.geekatplay.com")
    
    print()
    input("Press Enter to exit...")