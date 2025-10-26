# ComfyUI HiTem3D Integration

A custom ComfyUI node that integrates with the HiTem3D API to generate high-quality 3D models from images.

**Created by:** Geekatplay Studio by Vladimir Chopine  
**Website:** [www.geekatplay.com](https://www.geekatplay.com)  
**Patreon:** [https://www.patreon.com/c/geekatplay](https://www.patreon.com/c/geekatplay)  
**YouTube:** [@geekatplay](https://www.youtube.com/@geekatplay) and [@geekatplay-ru](https://www.youtube.com/@geekatplay-ru)  

## 💰 Get HiTem3D Credits
**Special Referral Link:** [https://www.hitem3d.ai/?sp_source=Geekatplay](https://www.hitem3d.ai/?sp_source=Geekatplay)  
Use this link to sign up and get credits for HiTem3D API usage!

## 🚀 Quick Start

**⚠️ SETUP REQUIRED:** This node requires your personal HiTem3D API keys!

1. **Run Setup Wizard:**
   ```cmd
   # Windows
   setup_wizard.bat
   
   # Linux/Mac
   python setup_wizard.py
   ```

2. **Get API Keys:** [https://www.hitem3d.ai/?sp_source=Geekatplay](https://www.hitem3d.ai/?sp_source=Geekatplay)

3. **Add Credits** to your HiTem3D account

4. **Restart ComfyUI** and try the example workflows!

📖 **Detailed Setup:** See `QUICK_SETUP.md`

## Features

- **Image to 3D Generation**: Convert single images to 3D models
- **Multi-view Support**: Use front, back, left, and right images for better results
- **Multiple Output Formats**: Support for OBJ, GLB, STL, and FBX formats
- **Flexible Generation Types**: Geometry-only, texture-only, or complete generation
- **Multiple Model Versions**: Support for v1.0, v1.5, and portrait-specific models
- **Configurable Parameters**: Resolution, face count, and other generation parameters

## Installation

1. The custom node is already installed in your ComfyUI directory:
   ```
   ComfyUI/custom_nodes/comfyui-hitem3d/
   ```

2. Install the required dependencies using one of these methods:

   **Method 1 - PowerShell (Recommended):**
   ```powershell
   cd "ComfyUI/custom_nodes/comfyui-hitem3d"
   & "../../python_embeded/python.exe" -m pip install -r requirements.txt
   ```

   **Method 2 - Use the installation script:**
   ```powershell
   cd "ComfyUI/custom_nodes/comfyui-hitem3d"
   .\install_direct.bat
   ```

   **Method 3 - PowerShell script:**
   ```powershell
   cd "ComfyUI/custom_nodes/comfyui-hitem3d"
   .\install.ps1
   ```

3. The configuration file `config.json` is already set up with your API credentials.

4. Restart ComfyUI

## API Credentials

To use this node, you need HiTem3D API credentials:

1. **Get Credits:** Visit [https://www.hitem3d.ai/?sp_source=Geekatplay](https://www.hitem3d.ai/?sp_source=Geekatplay) to sign up with referral code
2. **Purchase a resource package** (required for generating 3D models)
3. Create an API key in the developer console
4. Use the Access Key and Secret Key in the configuration

### Initial Setup Required

**⚠️ IMPORTANT: You need to configure your personal API keys before using this node!**

1. **Get Your API Keys:**
   - Visit [https://www.hitem3d.ai/?sp_source=Geekatplay](https://www.hitem3d.ai/?sp_source=Geekatplay)
   - Register/Login to your account
   - Navigate to the API/Developer section
   - Generate your personal Access Key and Secret Key

2. **Configure the Node:**
   - Run the setup wizard: `python setup_wizard.py`
   - Or manually edit `config.json` with your keys
   - Or use the `HiTem3DConfigNode` in ComfyUI

### ⚠️ Important: Account Balance Required

**Your API credentials are valid, but you need to add credits to your account to generate 3D models.**

If you see errors like "余额不足" or "Insufficient balance":
1. Visit [https://www.hitem3d.ai/?sp_source=Geekatplay](https://www.hitem3d.ai/?sp_source=Geekatplay)
2. Log into your account
3. Purchase a resource package to add credits
4. Each 3D generation consumes credits based on resolution and complexity

### Test Your Account Status
```powershell
cd "ComfyUI/custom_nodes/comfyui-hitem3d"
& "../../python_embeded/python.exe" check_balance.py
```

## Usage

### Quick Start with Example Workflows

The easiest way to get started is to use the provided example workflows:

1. **Navigate to the examples directory**: `examples/`
2. **Choose a workflow**:
   - `hitem3d_simple_workflow.json` - Basic single image to 3D
   - `hitem3d_multiview_workflow.json` - Multi-view to 3D  
   - `hitem3d_config_workflow.json` - Configure API credentials
3. **Load the workflow** in ComfyUI (drag and drop the JSON file)
4. **Add your images** to ComfyUI's input folder
5. **Run the workflow**

See `examples/README.md` for detailed instructions.

### Manual Node Setup

### HiTem3D Generator Node

The main node for generating 3D models:

**Required Inputs:**
- `front_image`: The front view image (required)

**Optional Inputs:**
- `back_image`: Back view image (optional)
- `left_image`: Left side view image (optional) 
- `right_image`: Right side view image (optional)
- `model`: Model version (`hitem3dv1`, `hitem3dv1.5`, `scene-portraitv1.5`)
- `resolution`: Output resolution (`512`, `1024`, `1536`, `1536pro`)
- `output_format`: File format (`obj`, `glb`, `stl`, `fbx`)
- `generation_type`: Generation type (`geometry_only`, `texture_only`, `both`)
- `face_count`: Number of faces (100,000 - 2,000,000)
- `timeout`: Maximum wait time in seconds

**Outputs:**
- `model_url`: URL to download the generated 3D model
- `cover_url`: URL to download the preview image
- `task_id`: Unique task identifier

### HiTem3D Downloader Node

Downloads 3D models from HiTem3D URLs:

**Inputs:**
- `model_url`: URL from the Generator node
- `filename`: Base filename for the downloaded model
- `output_directory`: Directory to save the model (optional)

**Outputs:**
- `file_path`: Local path to the downloaded model file

### HiTem3D Config Node

Updates API configuration:

**Inputs:**
- `access_key`: Your HiTem3D access key
- `secret_key`: Your HiTem3D secret key
- `api_base_url`: API base URL (optional)
- `save_config`: Whether to save configuration to file

**Outputs:**
- `status`: Configuration update status message

## Workflow Example

1. **Load Image**: Use ComfyUI's Load Image node to load your front view image
2. **Optional**: Load additional images for back, left, and right views
3. **HiTem3D Generator**: Connect your images to the HiTem3D Generator node
4. **Configure Parameters**: Set your desired model version, resolution, and format
5. **Generate**: Run the workflow to create your 3D model
6. **Download**: Use the HiTem3D Downloader node to save the model locally

## Supported Parameters

### Model Versions
- `hitem3dv1`: General model version 1.0
- `hitem3dv1.5`: General model version 1.5 (recommended)
- `scene-portraitv1.5`: Specialized for portrait/character models

### Resolutions
- `512`: 512³ resolution
- `1024`: 1024³ resolution (recommended)
- `1536`: 1536³ resolution
- `1536pro`: 1536³ Pro resolution (highest quality)

### Output Formats
- `obj`: Wavefront OBJ format
- `glb`: Binary glTF format (recommended)
- `stl`: STL format (for 3D printing)
- `fbx`: Autodesk FBX format

### Generation Types
- `geometry_only`: Generate only the mesh geometry
- `texture_only`: Generate textures for existing geometry (requires mesh_url)
- `both`: Generate both geometry and textures (recommended)

## Troubleshooting

### Common Issues

1. **"Config file not found"**: Ensure `config.json` exists in the node directory
2. **"Invalid credentials"**: Check your access key and secret key
3. **"Task timeout"**: Increase the timeout value or check API status
4. **"Insufficient balance"**: Contact HiTem3D support to add credits

## Troubleshooting

### Common Issues

1. **"Insufficient balance" (余额不足)**: Your account needs more credits
   - Visit [https://www.hitem3d.ai/?sp_source=Geekatplay](https://www.hitem3d.ai/?sp_source=Geekatplay) to purchase credits
   - Run `check_balance.py` to verify your account status

2. **"Invalid credentials"**: Check your access key and secret key
3. **"Task timeout"**: Increase the timeout value or try lower resolution
4. **"Upload file size exceeds limit"**: Ensure images are under 20MB

### Troubleshooting Tools

- **Balance Checker**: `check_balance.py` - Verify account and credentials
- **Troubleshooting Guide**: `TROUBLESHOOTING.md` - Comprehensive error solutions
- **Example Workflows**: `examples/` - Ready-to-use workflows for testing

For detailed troubleshooting, see `TROUBLESHOOTING.md`.

### API Limits

- Maximum image size: 20MB per image
- Maximum images: 4 images (front, back, left, right)
- Supported formats: PNG, JPEG, JPG, WebP
- Face count range: 100,000 - 2,000,000

### Logging

The node provides detailed logging information. Check the ComfyUI console for:
- Task creation status
- Generation progress
- Download status
- Error messages

## API Reference

For detailed API documentation, visit:
- [HiTem3D API Documentation](https://docs.hitem3d.ai/en/api/api-reference/)
- [Getting Started Guide](https://docs.hitem3d.ai/en/api/getting-started/)
- [Quick Start](https://docs.hitem3d.ai/en/api/getting-started/quickstart)

## Support

For issues related to:
- **This ComfyUI node**: Visit [www.geekatplay.com](https://www.geekatplay.com) or contact Geekatplay Studio
- **HiTem3D API**: Contact [apicontact@hitem3d.ai](mailto:apicontact@hitem3d.ai)
- **ComfyUI**: Check the [ComfyUI documentation](https://github.com/comfyanonymous/ComfyUI)

## Support Geekatplay Studio

If you find this node useful, please consider supporting:
- **Patreon:** [https://www.patreon.com/c/geekatplay](https://www.patreon.com/c/geekatplay)
- **YouTube:** [@geekatplay](https://www.youtube.com/@geekatplay) and [@geekatplay-ru](https://www.youtube.com/@geekatplay-ru)
- **Website:** [www.geekatplay.com](https://www.geekatplay.com)

## License

This project is created by Geekatplay Studio by Vladimir Chopine for integration with the HiTem3D API service.

## Version History

- **v1.0.0**: Initial release with full HiTem3D API integration
  - Single and multi-view image support
  - All model versions and formats
  - Configurable parameters
  - Automatic download functionality
  - Created by Geekatplay Studio