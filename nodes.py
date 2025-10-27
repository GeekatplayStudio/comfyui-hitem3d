"""
ComfyUI HiTem3D Nodes
Custom nodes for generating 3D models from images using HiTem3D API

Created by: Geekatplay Studio by Vladimir Chopine
Website: www.geekatplay.com
Patreon: https://www.patreon.com/c/geekatplay
YouTube: @geekatplay and @geekatplay-ru

Get HiTem3D credits with referral code: https://www.hitem3d.ai/?sp_source=Geekatplay
"""

import os
import io
import json
import time
import logging
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import torch
import numpy as np
from PIL import Image

# Import our HiTem3D client
try:
    from .hitem3d_client import HiTem3DAPIClient, create_client_from_config
except ImportError:
    # Fallback for direct execution
    from hitem3d_client import HiTem3DAPIClient, create_client_from_config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the current directory
CURRENT_DIR = Path(__file__).parent
CONFIG_PATH = CURRENT_DIR / "config.json"
TEMP_DIR = CURRENT_DIR / "temp"
TEMP_DIR.mkdir(exist_ok=True)


def tensor_to_image_bytes(tensor: torch.Tensor, format: str = "JPEG") -> bytes:
    """Convert ComfyUI image tensor to bytes"""
    # ComfyUI tensors are typically in format (batch, height, width, channels)
    if tensor.dim() == 4:
        tensor = tensor.squeeze(0)  # Remove batch dimension
    
    # Convert from tensor to numpy
    if tensor.is_cuda:
        tensor = tensor.cpu()
    
    # Convert to uint8 if needed
    if tensor.dtype != torch.uint8:
        tensor = (tensor * 255).clamp(0, 255).to(torch.uint8)
    
    numpy_image = tensor.numpy()
    
    # Convert to PIL Image
    pil_image = Image.fromarray(numpy_image)
    
    # Convert to bytes
    img_bytes = io.BytesIO()
    pil_image.save(img_bytes, format=format)
    return img_bytes.getvalue()


class HiTem3DNode:
    """
    ComfyUI node for generating 3D models using HiTem3D API
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "front_image": ("IMAGE",),
            },
            "optional": {
                "back_image": ("IMAGE",),
                "left_image": ("IMAGE",),
                "right_image": ("IMAGE",),
                "model": (["hitem3dv1", "hitem3dv1.5", "scene-portraitv1.5", "promodel"], {"default": "hitem3dv1.5"}),
                "resolution": ([512, 1024, 1536], {"default": 1024}),
                "output_format": (["obj", "glb", "stl", "fbx"], {"default": "glb"}),
                "generation_type": (["geometry_only", "texture_only", "both"], {"default": "both"}),
                "face_count": ("INT", {"default": 1000000, "min": 100000, "max": 2000000, "step": 10000}),
                "timeout": ("INT", {"default": 300, "min": 60, "max": 1800, "step": 30}),
                "config_data": ("STRING", {"default": ""}),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("model_url", "cover_url", "task_id")
    FUNCTION = "generate_3d_model"
    CATEGORY = "HiTem3D"
    
    def __init__(self):
        self.client = None
        # Don't auto-load client in __init__, load it when needed
    
    def _load_client(self, use_runtime_config=False):
        """Load HiTem3D API client from config file or runtime config"""
        try:
            # First try runtime config from ConfigNode
            if use_runtime_config:
                runtime_config = HiTem3DConfigNode.get_runtime_config()
                if runtime_config:
                    from hitem3d_comfyui.client import HiTem3DClient
                    self.client = HiTem3DClient(
                        access_key=runtime_config["access_key"],
                        secret_key=runtime_config["secret_key"],
                        api_base_url=runtime_config["api_base_url"]
                    )
                    logger.info("HiTem3D client loaded from runtime configuration")
                    return
            
            # Fallback to file config
            if CONFIG_PATH.exists():
                self.client = create_client_from_config(str(CONFIG_PATH))
                logger.info("HiTem3D client loaded from config file")
            else:
                logger.error(f"Config file not found: {CONFIG_PATH}")
                raise FileNotFoundError(f"Config file not found: {CONFIG_PATH}")
        except Exception as e:
            logger.error(f"Failed to load HiTem3D client: {str(e)}")
            raise
    
    def _format_to_int(self, format_str: str) -> int:
        """Convert format string to API integer"""
        format_map = {"obj": 1, "glb": 2, "stl": 3, "fbx": 4}
        return format_map.get(format_str, 2)
    
    def _generation_type_to_int(self, gen_type: str) -> int:
        """Convert generation type string to API integer"""
        type_map = {"geometry_only": 1, "texture_only": 2, "both": 3}
        return type_map.get(gen_type, 3)
    
    def _resolution_to_int(self, resolution) -> int:
        """Convert resolution to integer"""
        if isinstance(resolution, str) and resolution == "1536pro":
            return 1536  # API uses 1536 for pro, differentiated by other params
        return int(resolution)
    
    def generate_3d_model(self, 
                         front_image: torch.Tensor,
                         back_image: Optional[torch.Tensor] = None,
                         left_image: Optional[torch.Tensor] = None,
                         right_image: Optional[torch.Tensor] = None,
                         model: str = "hitem3dv1.5",
                         resolution = 1024,
                         output_format: str = "glb",
                         generation_type: str = "both",
                         face_count: int = 1000000,
                         timeout: int = 300,
                         config_data: str = "") -> Tuple[str, str, str]:
        """
        Generate 3D model from input images and wait for completion
        
        Returns:
            Tuple containing (model_url, cover_url, task_id)
        """
        try:
            # Try to load client with runtime config first, then fallback to file config
            if self.client is None:
                try:
                    self._load_client(use_runtime_config=True)
                except:
                    self._load_client(use_runtime_config=False)
            
            logger.info("Starting 3D model generation...")
            
            # Convert images to bytes
            front_bytes = tensor_to_image_bytes(front_image)
            back_bytes = tensor_to_image_bytes(back_image) if back_image is not None else None
            left_bytes = tensor_to_image_bytes(left_image) if left_image is not None else None
            right_bytes = tensor_to_image_bytes(right_image) if right_image is not None else None
            
            # Convert parameters (back to integers for API)
            format_int = self._format_to_int(output_format)
            request_type = self._generation_type_to_int(generation_type)
            resolution_int = self._resolution_to_int(resolution)
            
            # Create task
            logger.info("Creating generation task...")
            task_id = self.client.create_task(
                front_image=front_bytes,
                back_image=back_bytes,
                left_image=left_bytes,
                right_image=right_bytes,
                model=model,
                resolution=resolution_int,
                face_count=face_count,
                output_format=format_int,
                request_type=request_type
            )
            
            logger.info(f"Task created: {task_id}")
            logger.info("Waiting for task completion...")
            
            # Wait for task completion
            result = self.client.wait_for_completion(task_id, timeout)
            
            if result.get('status') == 'completed':
                model_url = result.get('url', '')
                cover_url = result.get('cover_url', '')
                
                # Check if we got a valid model URL
                if model_url:
                    logger.info("✅ GENERATION COMPLETED! Model and cover URLs ready.")
                    logger.info(f"Model URL: {model_url}")
                    logger.info(f"Cover URL: {cover_url}")
                    return (model_url, cover_url, task_id)
                else:
                    # Task completed but no URL - log the full result for debugging
                    logger.error(f"❌ GENERATION COMPLETED but no model URL found. Result: {result}")
                    return ("❌ GENERATION COMPLETED but no model URL returned", "", task_id)
            else:
                error_msg = result.get('error', f"Task status: {result.get('status', 'unknown')}")
                logger.error(f"❌ GENERATION FAILED: {error_msg}")
                return ("", "", task_id)
            
        except Exception as e:
            error_msg = str(e)
            
            # Handle specific error cases with user-friendly messages
            if "Insufficient balance" in error_msg or "余额不足" in error_msg:
                error_msg = "❌ INSUFFICIENT CREDITS: Your HiTem3D account balance is too low. Please visit https://www.hitem3d.ai/?sp_source=Geekatplay to add credits."
            elif "Invalid credentials" in error_msg or "client credentials are invalid" in error_msg:
                error_msg = "❌ INVALID API CREDENTIALS: Please check your Access Key and Secret Key in the configuration."
            elif "timeout" in error_msg.lower():
                error_msg = "⏱️ TIMEOUT: 3D generation took too long. Try increasing the timeout value or try again later."
            elif "Failed to get access token" in error_msg:
                error_msg = "🔑 AUTHENTICATION FAILED: Unable to get access token. Check your API credentials and internet connection."
            else:
                error_msg = f"❌ GENERATION FAILED: {error_msg}"
            
            logger.error(error_msg)
            return (error_msg, "", "")


class HiTem3DDownloaderNode:
    """
    ComfyUI node for downloading 3D models from HiTem3D task results
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_url": ("STRING", {"default": ""}),
                "file_name": ("STRING", {"default": "model"}),
                "output_directory": ("STRING", {"default": "ComfyUI/output/hitem3d/"}),
            },
            "optional": {
                "config_data": ("STRING", {"default": ""}),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("model_path", "status")
    FUNCTION = "download_model"
    CATEGORY = "HiTem3D"
    OUTPUT_NODE = True
    
    def __init__(self):
        self.client = None
        # Don't auto-load client in __init__, load it when needed
    
    def _load_client(self, use_runtime_config=False):
        """Load HiTem3D API client from config file or runtime config"""
        try:
            # First try runtime config from ConfigNode
            if use_runtime_config:
                runtime_config = HiTem3DConfigNode.get_runtime_config()
                if runtime_config:
                    from hitem3d_comfyui.client import HiTem3DClient
                    self.client = HiTem3DClient(
                        access_key=runtime_config["access_key"],
                        secret_key=runtime_config["secret_key"],
                        api_base_url=runtime_config["api_base_url"]
                    )
                    logger.info("HiTem3D client loaded from runtime configuration")
                    return
            
            # Fallback to file config
            if CONFIG_PATH.exists():
                self.client = create_client_from_config(str(CONFIG_PATH))
                logger.info("HiTem3D client loaded from config file")
            else:
                logger.error(f"Config file not found: {CONFIG_PATH}")
                raise FileNotFoundError(f"Config file not found: {CONFIG_PATH}")
        except Exception as e:
            logger.error(f"Failed to load HiTem3D client: {str(e)}")
            raise
    
    def _load_client(self, use_runtime_config=False):
        """Load HiTem3D API client from config file or runtime config"""
        try:
            # First try runtime config from ConfigNode
            if use_runtime_config:
                runtime_config = HiTem3DConfigNode.get_runtime_config()
                if runtime_config:
                    from hitem3d_comfyui.client import HiTem3DClient
                    self.client = HiTem3DClient(
                        access_key=runtime_config["access_key"],
                        secret_key=runtime_config["secret_key"],
                        api_base_url=runtime_config.get("api_base_url", "https://api.hitem3d.ai")
                    )
                    logger.info("HiTem3D client loaded from runtime config")
                    return
            
            # Fallback to config file
            if CONFIG_PATH.exists():
                self.client = create_client_from_config(str(CONFIG_PATH))
                logger.info("HiTem3D client loaded from config file")
            else:
                logger.error(f"Config file not found: {CONFIG_PATH}")
                raise FileNotFoundError(f"Config file not found: {CONFIG_PATH}")
        except Exception as e:
            logger.error(f"Failed to load HiTem3D client: {str(e)}")
            raise
    
    def download_model(self, 
                         model_url: str,
                         file_name: str = "model",
                         output_directory: str = "ComfyUI/output/hitem3d/",
                         config_data: str = "") -> Tuple[str, str]:
        """
        Download 3D model from provided URL
        
        Returns:
            Tuple containing (model_path, status)
        """
        try:
            # Try to load client with runtime config first, then fallback to file config
            if self.client is None:
                try:
                    self._load_client(use_runtime_config=True)
                except:
                    self._load_client(use_runtime_config=False)
            
            if not model_url or model_url.startswith("❌"):
                return (f"❌ DOWNLOAD FAILED: Invalid model URL: {model_url}", "Failed")
            
            # Determine file extension from URL
            if model_url.endswith('.glb'):
                extension = '.glb'
            elif model_url.endswith('.obj'):
                extension = '.obj'
            elif model_url.endswith('.stl'):
                extension = '.stl'
            elif model_url.endswith('.fbx'):
                extension = '.fbx'
            else:
                extension = '.glb'  # Default
            
            # Create timestamped filename to avoid overwriting
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{file_name}_{timestamp}{extension}"
            
            # Create output path
            output_dir = Path(output_directory)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_path = output_dir / filename
            
            # Download the model
            logger.info(f"Downloading model from: {model_url}")
            downloaded_path = self.client.download_model(model_url, str(output_path))
            
            logger.info(f"Model downloaded to: {downloaded_path}")
            return (downloaded_path, "Downloaded successfully")
            
        except Exception as e:
            error_msg = str(e)
            if "timeout" in error_msg.lower():
                error_msg = "⏱️ TIMEOUT: Task is taking longer than expected. You can increase timeout or check status later."
            elif "Task failed" in error_msg:
                error_msg = "❌ GENERATION FAILED: The 3D model generation task failed on the server."
            else:
                error_msg = f"❌ DOWNLOAD FAILED: {error_msg}"
            
            logger.error(error_msg)
            return (error_msg, "Failed")
            
            logger.error(error_msg)
            return (error_msg,)


class HiTem3DConfigNode:
    """
    ComfyUI node for configuring HiTem3D API credentials
    Provides runtime configuration for other HiTem3D nodes
    """
    
    # Class variable to store runtime config
    _runtime_config = None
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "access_key": ("STRING", {"default": "YOUR_ACCESS_KEY_HERE"}),
                "secret_key": ("STRING", {"default": "YOUR_SECRET_KEY_HERE"}),
            },
            "optional": {
                "api_base_url": ("STRING", {"default": "https://api.hitem3d.ai"}),
                "save_config": ("BOOLEAN", {"default": False}),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("config_status", "config_data")
    FUNCTION = "update_config"
    CATEGORY = "HiTem3D"
    OUTPUT_NODE = True
    
    def update_config(self, 
                     access_key: str,
                     secret_key: str,
                     api_base_url: str = "https://api.hitem3d.ai",
                     save_config: bool = False) -> Tuple[str, str]:
        """
        Update HiTem3D API configuration
        
        Returns:
            Tuple containing (status_message, config_data)
        """
        try:
            if not access_key or not secret_key or access_key == "YOUR_ACCESS_KEY_HERE" or secret_key == "YOUR_SECRET_KEY_HERE":
                return ("⚠️ CONFIGURATION REQUIRED: Please enter your HiTem3D API credentials", "")
            
            config = {
                "hitem3d": {
                    "access_key": access_key,
                    "secret_key": secret_key,
                    "api_base_url": api_base_url,
                    "default_model": "hitem3dv1.5",
                    "default_resolution": 1024,
                    "default_format": 2,
                    "default_face_count": 1000000,
                    "timeout": 300
                }
            }
            
            # Store runtime config for other nodes to use
            HiTem3DConfigNode._runtime_config = config["hitem3d"]
            
            if save_config:
                with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4)
                
                logger.info("Configuration updated and saved to file")
                return ("✅ Configuration updated and saved successfully", str(config))
            else:
                logger.info("Configuration updated (runtime only, not saved to file)")
                return ("✅ Configuration updated (runtime only, not saved to file)", str(config))
                
        except Exception as e:
            error_msg = f"Failed to update configuration: {str(e)}"
            logger.error(error_msg)
            return (f"❌ ERROR: {error_msg}", "")
    
    @classmethod
    def get_runtime_config(cls):
        """Get current runtime configuration"""
        return cls._runtime_config


class HiTem3DPreviewNode:
    """
    ComfyUI node for previewing 3D models generated by HiTem3D
    Created by: Geekatplay Studio by Vladimir Chopine
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_path": ("STRING", {"default": "", "multiline": False}),
            },
            "optional": {
                "width": ("INT", {"default": 512, "min": 256, "max": 2048, "step": 64}),
                "height": ("INT", {"default": 400, "min": 256, "max": 2048, "step": 64}),
                "background_color": (["#000000", "#FFFFFF", "#808080", "#f0f0f0"], {"default": "#f0f0f0"}),
                "auto_rotate": ("BOOLEAN", {"default": True}),
                "show_wireframe": ("BOOLEAN", {"default": False}),
                "show_grid": ("BOOLEAN", {"default": True}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("preview_html",)
    FUNCTION = "preview_3d_model"
    CATEGORY = "HiTem3D"
    OUTPUT_NODE = True
    
    def preview_3d_model(self, model_path, width=512, height=400, background_color="#f0f0f0", 
                         auto_rotate=True, show_wireframe=False, show_grid=True):
        """Generate HTML preview of 3D model"""
        try:
            import os
            import base64
            from pathlib import Path
            
            if not model_path or not os.path.exists(model_path):
                return (self._create_error_preview("Model file not found", width, height),)
            
            # Get file extension to determine model type
            file_ext = Path(model_path).suffix.lower()
            supported_formats = ['.obj', '.glb', '.gltf', '.stl', '.fbx']
            
            if file_ext not in supported_formats:
                return (self._create_error_preview(f"Unsupported format: {file_ext}", width, height),)
            
            # Read model file
            try:
                with open(model_path, 'rb') as f:
                    model_data = f.read()
                
                # Encode as base64 for embedding
                model_base64 = base64.b64encode(model_data).decode('utf-8')
                
                # Create HTML preview
                html_preview = self._create_3d_preview_html(
                    model_base64, file_ext, width, height, 
                    background_color, auto_rotate, show_wireframe, show_grid
                )
                
                return (html_preview,)
                
            except Exception as e:
                return (self._create_error_preview(f"Error reading model: {str(e)}", width, height),)
                
        except Exception as e:
            logger.error(f"3D Preview Error: {e}")
            return (self._create_error_preview(f"Preview error: {str(e)}", width, height),)
    
    def _create_3d_preview_html(self, model_data, file_ext, width, height, 
                               background_color, auto_rotate, wireframe, show_grid):
        """Create HTML with Three.js for 3D model preview"""
        
        # Determine loader based on file extension
        loader_code = self._get_loader_code(file_ext)
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>HiTem3D Model Preview</title>
    <style>
        body {{ 
            margin: 0; 
            padding: 10px; 
            background: {background_color}; 
            font-family: Arial, sans-serif;
            color: white;
        }}
        #container {{ 
            width: {width}px; 
            height: {height}px; 
            border: 2px solid #555;
            border-radius: 8px;
            overflow: hidden;
            position: relative;
        }}
        #info {{ 
            position: absolute; 
            top: 10px; 
            left: 10px; 
            background: rgba(0,0,0,0.7); 
            padding: 8px; 
            border-radius: 4px;
            font-size: 12px;
            z-index: 100;
        }}
        #controls {{
            margin-top: 10px;
            padding: 10px;
            background: rgba(0,0,0,0.3);
            border-radius: 4px;
        }}
        .control-group {{
            margin: 5px 0;
        }}
        button {{
            background: #4CAF50;
            color: white;
            border: none;
            padding: 5px 10px;
            margin: 2px;
            border-radius: 3px;
            cursor: pointer;
            font-size: 11px;
        }}
        button:hover {{ background: #45a049; }}
        .credit {{
            text-align: center;
            font-size: 10px;
            margin-top: 5px;
            opacity: 0.7;
        }}
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/OBJLoader.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/STLLoader.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/FBXLoader.js"></script>
</head>
<body>
    <div id="container"></div>
    <div id="info">
        🎯 HiTem3D Model Preview<br>
        Format: {file_ext.upper()}<br>
        <span id="stats">Loading...</span>
    </div>
    
    <div id="controls">
        <div class="control-group">
            <button onclick="resetCamera()">Reset View</button>
            <button onclick="toggleWireframe()">Wireframe</button>
            <button onclick="toggleRotation()">Auto Rotate</button>
            <button onclick="toggleGrid()">Grid</button>
        </div>
        <div class="control-group">
            <button onclick="changeBackground('#000000')">Black</button>
            <button onclick="changeBackground('#FFFFFF')">White</button>
            <button onclick="changeBackground('#404040')">Gray</button>
        </div>
    </div>
    
    <div class="credit">
        Created by: Geekatplay Studio by Vladimir Chopine | 
        <a href="https://www.geekatplay.com" style="color: #4CAF50;">www.geekatplay.com</a>
    </div>

    <script>
        let scene, camera, renderer, controls, model, mixer;
        let autoRotate = {str(auto_rotate).lower()};
        let wireframe = {str(wireframe).lower()};
        let showGrid = {str(show_grid).lower()};
        
        init();
        loadModel();
        animate();
        
        function init() {{
            const container = document.getElementById('container');
            
            // Scene
            scene = new THREE.Scene();
            scene.background = new THREE.Color('{background_color}');
            
            // Camera
            camera = new THREE.PerspectiveCamera(75, {width}/{height}, 0.1, 1000);
            camera.position.set(0, 0, 5);
            
            // Renderer
            renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setSize({width}, {height});
            renderer.shadowMap.enabled = true;
            renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            container.appendChild(renderer.domElement);
            
            // Controls
            controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            controls.autoRotate = autoRotate;
            controls.autoRotateSpeed = 2.0;
            
            // Lighting
            const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
            scene.add(ambientLight);
            
            const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
            directionalLight.position.set(1, 1, 1);
            directionalLight.castShadow = true;
            scene.add(directionalLight);
            
            const light2 = new THREE.DirectionalLight(0xffffff, 0.4);
            light2.position.set(-1, -1, -1);
            scene.add(light2);
            
            // Grid
            if (showGrid) {{
                const gridHelper = new THREE.GridHelper(10, 10);
                gridHelper.name = 'grid';
                scene.add(gridHelper);
            }}
        }}
        
        function loadModel() {{
            const modelData = '{model_data}';
            {loader_code}
        }}
        
        function animate() {{
            requestAnimationFrame(animate);
            controls.update();
            if (mixer) mixer.update(0.016);
            renderer.render(scene, camera);
        }}
        
        // Control functions
        function resetCamera() {{
            camera.position.set(0, 0, 5);
            controls.reset();
        }}
        
        function toggleWireframe() {{
            wireframe = !wireframe;
            if (model) {{
                model.traverse(function(child) {{
                    if (child.isMesh) {{
                        child.material.wireframe = wireframe;
                    }}
                }});
            }}
        }}
        
        function toggleRotation() {{
            autoRotate = !autoRotate;
            controls.autoRotate = autoRotate;
        }}
        
        function toggleGrid() {{
            const grid = scene.getObjectByName('grid');
            if (grid) {{
                grid.visible = !grid.visible;
            }}
        }}
        
        function changeBackground(color) {{
            scene.background = new THREE.Color(color);
        }}
        
        function updateStats(vertices, faces) {{
            document.getElementById('stats').innerHTML = 
                `Vertices: ${{vertices}}<br>Faces: ${{faces}}`;
        }}
    </script>
</body>
</html>"""
        return html
    
    def _get_loader_code(self, file_ext):
        """Get appropriate Three.js loader code for file format"""
        if file_ext in ['.glb', '.gltf']:
            return """
            const loader = new THREE.GLTFLoader();
            const blob = new Blob([Uint8Array.from(atob(modelData), c => c.charCodeAt(0))]);
            const url = URL.createObjectURL(blob);
            
            loader.load(url, function(gltf) {
                model = gltf.scene;
                scene.add(model);
                
                // Center and scale model
                const box = new THREE.Box3().setFromObject(model);
                const center = box.getCenter(new THREE.Vector3());
                const size = box.getSize(new THREE.Vector3());
                const maxAxis = Math.max(size.x, size.y, size.z);
                const scale = 3 / maxAxis;
                
                model.scale.multiplyScalar(scale);
                model.position.sub(center.multiplyScalar(scale));
                
                // Setup animations if available
                if (gltf.animations && gltf.animations.length) {
                    mixer = new THREE.AnimationMixer(model);
                    gltf.animations.forEach((clip) => {
                        mixer.clipAction(clip).play();
                    });
                }
                
                // Count vertices and faces
                let vertices = 0, faces = 0;
                model.traverse(function(child) {
                    if (child.isMesh) {
                        vertices += child.geometry.attributes.position.count;
                        faces += child.geometry.index ? child.geometry.index.count / 3 : child.geometry.attributes.position.count / 3;
                    }
                });
                updateStats(vertices, Math.floor(faces));
                
                URL.revokeObjectURL(url);
            });"""
        
        elif file_ext == '.obj':
            return """
            const loader = new THREE.OBJLoader();
            const blob = new Blob([Uint8Array.from(atob(modelData), c => c.charCodeAt(0))]);
            const url = URL.createObjectURL(blob);
            
            loader.load(url, function(object) {
                model = object;
                scene.add(model);
                
                // Center and scale model
                const box = new THREE.Box3().setFromObject(model);
                const center = box.getCenter(new THREE.Vector3());
                const size = box.getSize(new THREE.Vector3());
                const maxAxis = Math.max(size.x, size.y, size.z);
                const scale = 3 / maxAxis;
                
                model.scale.multiplyScalar(scale);
                model.position.sub(center.multiplyScalar(scale));
                
                // Add basic material
                model.traverse(function(child) {
                    if (child.isMesh) {
                        child.material = new THREE.MeshLambertMaterial({ color: 0x888888 });
                        child.castShadow = true;
                        child.receiveShadow = true;
                    }
                });
                
                // Count vertices and faces
                let vertices = 0, faces = 0;
                model.traverse(function(child) {
                    if (child.isMesh) {
                        vertices += child.geometry.attributes.position.count;
                        faces += child.geometry.index ? child.geometry.index.count / 3 : child.geometry.attributes.position.count / 3;
                    }
                });
                updateStats(vertices, Math.floor(faces));
                
                URL.revokeObjectURL(url);
            });"""
        
        elif file_ext == '.stl':
            return """
            const loader = new THREE.STLLoader();
            const blob = new Blob([Uint8Array.from(atob(modelData), c => c.charCodeAt(0))]);
            const url = URL.createObjectURL(blob);
            
            loader.load(url, function(geometry) {
                const material = new THREE.MeshLambertMaterial({ color: 0x888888 });
                model = new THREE.Mesh(geometry, material);
                scene.add(model);
                
                // Center and scale model
                geometry.computeBoundingBox();
                const center = geometry.boundingBox.getCenter(new THREE.Vector3());
                const size = geometry.boundingBox.getSize(new THREE.Vector3());
                const maxAxis = Math.max(size.x, size.y, size.z);
                const scale = 3 / maxAxis;
                
                model.scale.multiplyScalar(scale);
                model.position.sub(center.multiplyScalar(scale));
                
                model.castShadow = true;
                model.receiveShadow = true;
                
                // Count vertices and faces
                const vertices = geometry.attributes.position.count;
                const faces = geometry.index ? geometry.index.count / 3 : vertices / 3;
                updateStats(vertices, Math.floor(faces));
                
                URL.revokeObjectURL(url);
            });"""
        
        else:  # FBX and others
            return """
            document.getElementById('stats').innerHTML = 'Format not yet supported in preview';
            """
    
    def _create_error_preview(self, error_message, width, height):
        """Create error message preview"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>HiTem3D Preview Error</title>
    <style>
        body {{ 
            margin: 0; 
            padding: 20px; 
            background: #404040; 
            color: white; 
            font-family: Arial, sans-serif;
            text-align: center;
        }}
        .error-container {{ 
            width: {width}px; 
            height: {height}px; 
            border: 2px solid #ff4444;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #2a2a2a;
            margin: 0 auto;
        }}
        .error-content {{
            text-align: center;
        }}
        .error-icon {{
            font-size: 48px;
            color: #ff4444;
            margin-bottom: 10px;
        }}
        .credit {{
            margin-top: 10px;
            font-size: 10px;
            opacity: 0.7;
        }}
    </style>
</head>
<body>
    <div class="error-container">
        <div class="error-content">
            <div class="error-icon">⚠️</div>
            <h3>Preview Error</h3>
            <p>{error_message}</p>
            <p style="font-size: 12px; opacity: 0.7;">
                Supported formats: OBJ, GLB, GLTF, STL
            </p>
        </div>
    </div>
    <div class="credit">
        Created by: Geekatplay Studio by Vladimir Chopine | 
        <a href="https://www.geekatplay.com" style="color: #4CAF50;">www.geekatplay.com</a>
    </div>
</body>
</html>"""


# Node mappings for ComfyUI
NODE_CLASS_MAPPINGS = {
    "HiTem3DNode": HiTem3DNode,
    "HiTem3DDownloaderNode": HiTem3DDownloaderNode,
    "HiTem3DConfigNode": HiTem3DConfigNode,
    "HiTem3DPreviewNode": HiTem3DPreviewNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "HiTem3DNode": "HiTem3D Generator",
    "HiTem3DDownloaderNode": "HiTem3D Downloader", 
    "HiTem3DConfigNode": "HiTem3D Config",
    "HiTem3DPreviewNode": "HiTem3D 3D Preview",
}