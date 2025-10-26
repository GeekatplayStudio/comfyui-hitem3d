# HiTem3D Troubleshooting Guide

**Created by:** Geekatplay Studio by Vladimir Chopine  
**Website:** [www.geekatplay.com](https://www.geekatplay.com)  
**Patreon:** [https://www.patreon.com/c/geekatplay](https://www.patreon.com/c/geekatplay)  
**YouTube:** [@geekatplay](https://www.youtube.com/@geekatplay) and [@geekatplay-ru](https://www.youtube.com/@geekatplay-ru)  

## 💰 Get HiTem3D Credits
**Special Referral Link:** [https://www.hitem3d.ai/?sp_source=Geekatplay](https://www.hitem3d.ai/?sp_source=Geekatplay)

## ❌ "Insufficient Balance" Error (余额不足)

**Problem**: You're seeing errors like:
- `ERROR: Failed to generate 3D model: Task creation failed: 余额不足`
- `Insufficient balance - Please add credits to your HiTem3D account`

**Solution**:
1. **Check Your Account Balance**:
   - Visit [https://www.hitem3d.ai/?sp_source=Geekatplay](https://www.hitem3d.ai/?sp_source=Geekatplay)
   - Log into your account using the same credentials
   - Check your credit balance and usage

2. **Add Credits**:
   - Purchase a resource package from the developer platform
   - Use the Geekatplay referral link for special offers
   - Credits are consumed per 3D generation request
   - Different resolutions and models consume different amounts

3. **Test Your Account**:
   ```powershell
   cd "ComfyUI/custom_nodes/comfyui-hitem3d"
   & "../../python_embeded/python.exe" check_balance.py
   ```

## 🔑 Authentication Issues

**Problem**: Invalid credentials or token errors

**Solution**:
1. **Get Your API Keys**:
   - Visit [https://www.hitem3d.ai/?sp_source=Geekatplay](https://www.hitem3d.ai/?sp_source=Geekatplay)
   - Register/Login to your account
   - Go to API/Developer section to get your personal keys
   - Access Key: `ak_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - Secret Key: `sk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

2. **Update Configuration**:
   - Use the `HiTem3DConfigNode` in ComfyUI
   - Or manually edit `config.json`

3. **Test Credentials**:
   - Run the balance checker script above
   - Check if you can obtain an access token

## ⏱️ Timeout Issues

**Problem**: Generation takes too long and times out

**Solution**:
1. **Increase Timeout**:
   - Default: 300 seconds (5 minutes)
   - Try: 600 seconds (10 minutes) for complex models
   - Maximum recommended: 1800 seconds (30 minutes)

2. **Use Lower Settings**:
   - Resolution: Start with 512, then try 1024
   - Generation Type: Try "geometry_only" first
   - Face Count: Reduce to 500,000 for faster generation

## 🌐 Network Issues

**Problem**: Connection errors or API unreachable

**Solution**:
1. **Check Internet Connection**
2. **Verify API Endpoint**: `https://api.hitem3d.ai`
3. **Firewall**: Ensure ComfyUI can access external APIs
4. **VPN**: Some VPNs may block the API

## 📁 File Download Issues

**Problem**: Models don't download or save

**Solution**:
1. **Check Permissions**: Ensure ComfyUI can write to the output directory
2. **Disk Space**: Verify you have enough space for 3D models
3. **Path Issues**: Check that output directory exists and is accessible

## 🔧 Quick Diagnostic Steps

### 1. Test Basic Functionality
```powershell
# Navigate to the custom node directory
cd "ComfyUI/custom_nodes/comfyui-hitem3d"

# Test API client import
& "../../python_embeded/python.exe" -c "from hitem3d_client import HiTem3DAPIClient; print('✅ Import successful')"

# Check account status
& "../../python_embeded/python.exe" check_balance.py
```

### 2. Load Example Workflow
1. Load `examples/hitem3d_simple_workflow.json`
2. Add a small test image (< 1MB)
3. Use these settings for testing:
   - Model: `hitem3dv1.5`
   - Resolution: `512`
   - Format: `glb`
   - Generation Type: `geometry_only`
   - Face Count: `500000`
   - Timeout: `600`

### 3. Check ComfyUI Logs
Look for specific error messages in the ComfyUI console output.

## 💰 Credit Management

### Typical Credit Consumption
- **512³ resolution**: ~1-2 credits
- **1024³ resolution**: ~3-5 credits  
- **1536³ resolution**: ~8-12 credits
- **Multi-view**: May consume more credits

### Reducing Credit Usage
1. **Start with lower resolution** (512)
2. **Use geometry_only** for testing
3. **Single image** instead of multi-view
4. **Test with small, simple objects** first

## 📞 Getting Help

### HiTem3D Support
- **Get Credits**: [https://www.hitem3d.ai/?sp_source=Geekatplay](https://www.hitem3d.ai/?sp_source=Geekatplay)
- **Email**: apicontact@hitem3d.ai
- **Documentation**: https://docs.hitem3d.ai/

### ComfyUI Node Support
- **Creator**: Geekatplay Studio by Vladimir Chopine
- **Website**: [www.geekatplay.com](https://www.geekatplay.com)
- **YouTube**: [@geekatplay](https://www.youtube.com/@geekatplay) and [@geekatplay-ru](https://www.youtube.com/@geekatplay-ru)
- **Patreon**: [https://www.patreon.com/c/geekatplay](https://www.patreon.com/c/geekatplay)
- Check the `examples/README.md` for workflow guidance
- Verify all dependencies are installed
- Ensure ComfyUI is up to date

### Common Error Codes
- **30010000**: Insufficient balance
- **40010000**: Invalid credentials
- **10031001**: File size too large (> 20MB)
- **10031002**: Invalid face count
- **10031003**: Invalid resolution
- **50010001**: Generation failed/timeout

## ✅ Success Checklist

Before reporting issues, verify:
- [ ] API credentials are correct
- [ ] Account has sufficient credits
- [ ] Test image is < 20MB
- [ ] Using supported image format (PNG, JPEG, JPG, WebP)
- [ ] ComfyUI can access the internet
- [ ] All dependencies are installed
- [ ] Using provided example workflows

If all items are checked and you still have issues, the problem is likely with the HiTem3D service or your account configuration.

---

**Support Geekatplay Studio:**
- **Patreon:** [https://www.patreon.com/c/geekatplay](https://www.patreon.com/c/geekatplay)
- **YouTube:** [@geekatplay](https://www.youtube.com/@geekatplay) and [@geekatplay-ru](https://www.youtube.com/@geekatplay-ru)
- **Website:** [www.geekatplay.com](https://www.geekatplay.com)