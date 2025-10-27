# HiTem3D ComfyUI Workflow Examples

**Created by:** Geekatplay Studio by Vladimir Chopine  
**Website:** [www.geekatplay.com](https://www.geekatplay.com)  
**Patreon:** [https://www.patreon.com/c/geekatplay](https://www.patreon.com/c/geekatplay)  
**YouTube:** [@geekatplay](https://www.youtube.com/@geekatplay) and [@geekatplay-ru](https://www.youtube.com/@geekatplay-ru)  

## 💰 Get HiTem3D Credits
**Special Referral Link:** [https://www.hitem3d.ai/?sp_source=Geekatplay](https://www.hitem3d.ai/?sp_source=Geekatplay)  
Use this link to sign up and get credits for HiTem3D API usage!

This directory contains example workflows demonstrating how to use the HiTem3D custom nodes in ComfyUI.

## Available Workflows

### 1. `hitem3d_simple_workflow.json` - Basic Single Image to 3D
**Purpose**: Generate a 3D model from a single front-view image.

**Nodes Used**:
- LoadImage: Load your input image
- HiTem3DNode: Generate 3D model from the image
- HiTem3DDownloaderNode: Download the generated model

### 2. `hitem3d_with_preview_workflow.json` - 3D Generation with Live Preview ⭐ NEW!
**Purpose**: Generate a 3D model and preview it directly in ComfyUI with interactive 3D viewer.

**Nodes Used**:
- LoadImage: Load your input image
- HiTem3DNode: Generate 3D model from the image
- HiTem3DDownloaderNode: Download the generated model
- **HiTem3DPreviewNode**: Interactive 3D model preview with controls

**Preview Features**:
- 🔄 Interactive rotation and zoom
- 🎨 Multiple background colors
- 🔍 Wireframe mode toggle
- 📐 Grid display
- 📊 Vertex and face count
- ⚡ Auto-rotation mode
- 🎮 Reset camera controls

**Supported Formats for Preview**:
- GLB/GLTF (recommended - best support)
- OBJ (with basic material)
- STL (solid models)
- FBX (partial support)

### 3. `hitem3d_multiview_workflow.json` - Advanced Multi-View Generation
- Model: `hitem3dv1.5` (latest version)
**How to Use**:
1. Load this workflow in ComfyUI
2. Upload an image using the LoadImage node
3. Configure generation parameters (model version, resolution, format)
4. Run the workflow
5. The 3D model will be generated, downloaded, and previewed automatically

**Recommended Settings**:
- Model: `hitem3dv1.5` (latest version)
- Resolution: `1024` (good balance of quality/speed)
- Format: `glb` (best for preview and widely supported)
- Generation Type: `both` (geometry + texture)

### 3. `hitem3d_multiview_workflow.json` - Multi-View to 3D
**Purpose**: Generate a high-quality 3D model from multiple view images.

**Nodes Used**:
- 4x LoadImage: Load front, back, left, and right view images
- HiTem3DNode: Generate 3D model from multiple views
- HiTem3DDownloaderNode: Download the generated model

**How to Use**:
1. Load this workflow in ComfyUI
2. Upload images for each view (front is required, others optional)
3. Configure generation parameters
4. Run the workflow

**Tips for Multi-View**:
- Ensure all images show the same object from different angles
- Use consistent lighting across all views
- Higher resolution (1536) recommended for better quality
- Increase face count (2,000,000) for more detail

### 4. `hitem3d_config_workflow.json` - API Configuration
**Purpose**: Update your HiTem3D API credentials.

**Nodes Used**:
- HiTem3DConfigNode: Configure API access keys

**How to Use**:
1. Load this workflow in ComfyUI
2. Enter your Access Key and Secret Key
3. Set save_config to true to persist the configuration
4. Run the workflow to update credentials

**Note**: The workflow comes pre-configured with the provided API keys.

## Loading Workflows

1. Open ComfyUI in your browser
2. Click "Load" button or drag and drop the JSON file
3. The workflow will be loaded with all nodes connected
4. Upload your images and configure parameters as needed
5. Click "Queue Prompt" to execute

## Common Parameters

### Model Versions
- `hitem3dv1`: General model v1.0
- `hitem3dv1.5`: General model v1.5 (recommended)
- `scene-portraitv1.5`: Specialized for portraits/characters

### Resolutions
- `512`: Fast generation, lower quality
- `1024`: Balanced quality and speed (recommended)
- `1536`: High quality, slower generation
- `1536pro`: Highest quality, longest generation time

### Output Formats
- `glb`: Binary glTF (recommended, widely supported)
- `obj`: Wavefront OBJ (with textures)
- `stl`: STL format (for 3D printing, geometry only)
- `fbx`: Autodesk FBX (for game engines)

### Generation Types
- `geometry_only`: Generate mesh only (fastest)
- `texture_only`: Add textures to existing geometry
- `both`: Complete model with geometry and textures (recommended)

## Troubleshooting

### "Prompt has no outputs" Error
This error occurs when workflows don't have output nodes. The provided workflows include the `HiTem3DDownloaderNode` which is marked as an output node and should resolve this issue.

### API Key Issues
If you get authentication errors:
1. Use the `hitem3d_config_workflow.json` to update your credentials
2. Check that your API keys are correct
3. Ensure you have sufficient credits in your HiTem3D account

### Long Generation Times
3D model generation can take several minutes:
- Lower resolution for faster results
- Use `geometry_only` for quickest generation
- Check the timeout setting (default: 300 seconds)

### File Download Issues
If models don't download:
- Check the output directory path
- Ensure you have write permissions
- Verify the model URL is valid

## 🎮 HiTem3D 3D Preview Node

The **HiTem3DPreviewNode** provides an interactive 3D viewer directly in ComfyUI!

### Features:
- **Interactive Controls**: Mouse to rotate, zoom, and pan
- **Multiple View Modes**: Solid, wireframe, with/without grid
- **Lighting**: Automatic lighting setup for optimal viewing
- **Background Options**: Black, white, gray backgrounds
- **Model Info**: Shows vertex and face counts
- **Format Support**: GLB, GLTF, OBJ, STL formats

### Controls:
- **Mouse**: Left-click drag to rotate, scroll to zoom, right-click drag to pan
- **Reset View**: Button to return to default camera position
- **Wireframe**: Toggle between solid and wireframe display
- **Auto Rotate**: Enable/disable automatic model rotation
- **Grid**: Show/hide reference grid
- **Background**: Quick background color changes

### Usage Tips:
- **GLB format recommended** for best preview experience
- **512x512 preview size** is good balance of quality and performance
- **Auto-rotate enabled** by default for better model visibility
- **File path** is automatically filled from HiTem3DDownloaderNode output

### Connection:
```
HiTem3DDownloaderNode (model_path) → HiTem3DPreviewNode (model_path)
```

The preview updates automatically when a new model is downloaded!

## Best Practices

1. **Image Quality**: Use high-resolution, well-lit images for best results
2. **Multi-View**: For complex objects, use multiple views for better accuracy
3. **Parameters**: Start with default settings and adjust based on your needs
4. **Testing**: Use lower resolution for testing, then increase for final output
5. **Storage**: Downloaded models are saved to `output/hitem3d/` by default

## Support

For issues with:
- **Workflows**: Check this README and try the simple workflow first
- **API**: Contact HiTem3D support at apicontact@hitem3d.ai
- **ComfyUI**: Check ComfyUI documentation and community forums
- **This Node**: Visit [www.geekatplay.com](https://www.geekatplay.com) or contact Geekatplay Studio

## Support Geekatplay Studio

If you find these workflows helpful, please consider supporting:
- **Patreon:** [https://www.patreon.com/c/geekatplay](https://www.patreon.com/c/geekatplay)
- **YouTube:** [@geekatplay](https://www.youtube.com/@geekatplay) and [@geekatplay-ru](https://www.youtube.com/@geekatplay-ru)
- **Website:** [www.geekatplay.com](https://www.geekatplay.com)
- **Get Credits:** [https://www.hitem3d.ai/?sp_source=Geekatplay](https://www.hitem3d.ai/?sp_source=Geekatplay)