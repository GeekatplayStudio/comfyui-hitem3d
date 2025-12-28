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
import urllib.parse
import uuid
import random
import datetime
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

# ComfyUI imports
import folder_paths

# HTML Previewer imports
try:
    from server import PromptServer
    from fastapi import HTTPException
    from fastapi.responses import HTMLResponse
    HTML_PREVIEWER_AVAILABLE = True
except ImportError:
    print("HTML Previewer: server imports not available, preview functionality disabled")
    HTML_PREVIEWER_AVAILABLE = False

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

# HTML Previewer configuration
ALLOWED_ROOTS = []
DEFAULT_INDEX = "index.html"

# Load allowed roots from environment variable
env_roots = os.getenv("HTML_PREVIEW_ALLOWED_ROOTS", "")
if env_roots:
    ALLOWED_ROOTS = [root.strip() for root in env_roots.split(";") if root.strip()]
else:
    # Default to ComfyUI output directory and temp directory
    output_dir = folder_paths.get_output_directory()
    if output_dir:
        ALLOWED_ROOTS.append(output_dir)
    ALLOWED_ROOTS.append(str(TEMP_DIR))

def _is_allowed(path: str) -> bool:
    """Check if a file path is allowed for HTML preview serving"""
    try:
        real = Path(path).resolve()
        
        # Must be a file with .html or .htm extension
        if not real.is_file() or real.suffix.lower() not in {".html", ".htm"}:
            return False
            
        # Check if path is within any allowed root
        for root in ALLOWED_ROOTS:
            try:
                root_path = Path(root).resolve()
                # Check if file is within this root directory
                try:
                    real.relative_to(root_path)
                    return True
                except ValueError:
                    # Not relative to this root, try next one
                    continue
            except Exception:
                continue
    except Exception:
        pass
    return False

# HTML Previewer HTTP Route
if HTML_PREVIEWER_AVAILABLE:
    @PromptServer.instance.routes.get("/html_previewer/open")
    def html_previewer_open(path: str = "", base: str = "", file: str = ""):
        """
        Serve a single HTML file:
          - Either provide ?path=C:\\...\\file.html
          - Or provide ?base=C:\\...\\folder&file=index.html
        """
        raw = path or os.path.join(base, file) if base and file else ""
        if not raw:
            raise HTTPException(status_code=400, detail="Missing 'path' or 'base'+'file'")

        # Normalize and validate
        decoded = urllib.parse.unquote(raw)
        if decoded.strip().startswith(("http://", "https://")):
            raise HTTPException(status_code=400, detail="Remote URLs are not allowed")

        if not _is_allowed(decoded):
            raise HTTPException(status_code=403, detail="Path not allowed")

        try:
            with open(decoded, "r", encoding="utf-8", errors="ignore") as f:
                html = f.read()
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="File not found")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Read error: {e}")

        # Basic CSP to reduce risk
        csp = "Content-Security-Policy"
        headers = {csp: "default-src 'self' 'unsafe-inline' data: blob:"}
        return HTMLResponse(content=html, headers=headers)


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
                "model": (["hitem3dv1", "hitem3dv1.5", "hitem3dv2.0", "scene-portraitv1.5"], {"default": "hitem3dv1.5"}),
                "resolution": ([512, 1024, 1536, "1536pro"], {"default": 1024}),
                "output_format": (["obj", "glb", "stl", "fbx"], {"default": "glb"}),
                "generation_type": (["geometry_only", "staged", "all_in_one"], {"default": "all_in_one"}),
                "face_count": ("INT", {"default": 1000000, "min": 100000, "max": 2000000, "step": 10000}),
                "timeout": ("INT", {"default": 900, "min": 300, "max": 7200, "step": 300}),
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
            # Check if runtime config should override file config
            if HiTem3DConfigNode.should_override_config():
                runtime_config = HiTem3DConfigNode.get_runtime_config()
                if runtime_config and runtime_config.get("access_key") and runtime_config.get("secret_key"):
                    from hitem3d_comfyui.client import HiTem3DClient
                    self.client = HiTem3DClient(
                        access_key=runtime_config["access_key"],
                        secret_key=runtime_config["secret_key"],
                        api_base_url=runtime_config.get("api_base_url", "https://api.hitem3d.ai")
                    )
                    logger.info("HiTem3D client loaded from runtime configuration (override enabled)")
                    return
            
            # First try runtime config from ConfigNode (if not overriding)
            if use_runtime_config:
                runtime_config = HiTem3DConfigNode.get_runtime_config()
                if runtime_config and runtime_config.get("access_key") and runtime_config.get("secret_key"):
                    from hitem3d_comfyui.client import HiTem3DClient
                    self.client = HiTem3DClient(
                        access_key=runtime_config["access_key"],
                        secret_key=runtime_config["secret_key"],
                        api_base_url=runtime_config.get("api_base_url", "https://api.hitem3d.ai")
                    )
                    logger.info("HiTem3D client loaded from runtime configuration")
                    return
            
            # Fallback to file config (only if it has valid keys and override is not enabled)
            if CONFIG_PATH.exists():
                # Check if config file has valid keys before using it
                import json
                with open(CONFIG_PATH, 'r') as f:
                    config = json.load(f)
                    hitem3d_config = config.get('hitem3d', {})
                    if hitem3d_config.get('access_key') and hitem3d_config.get('secret_key'):
                        self.client = create_client_from_config(str(CONFIG_PATH))
                        logger.info("HiTem3D client loaded from config file")
                        return
                    else:
                        logger.warning("Config file exists but API keys are empty")
            
            # If we get here, no valid config found
            raise ValueError("No valid API credentials found. Please configure them in the Config Node or in config.json")
            
        except Exception as e:
            logger.error(f"Failed to load HiTem3D client: {str(e)}")
            raise

    def _format_to_int(self, format_str: str) -> int:
        """Convert format string to API integer"""
        format_map = {"obj": 1, "glb": 2, "stl": 3, "fbx": 4}
        return format_map.get(format_str, 2)
    
    def _generation_type_to_int(self, gen_type: str) -> int:
        """Convert generation type string to API integer"""
        type_map = {"geometry_only": 1, "staged": 2, "all_in_one": 3, "texture_only": 2, "both": 3}
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
            
            # Log the full result for debugging
            logger.info(f"API result: {result}")
            
            # Check for success status (can be 'completed', 'success', or other variations)
            # API returns 'state' field, not 'status'
            status = result.get('state', result.get('status', '')).lower()
            logger.info(f"Final task status: {status}")
            
            if status in ['completed', 'success', 'finished']:
                model_url = result.get('url', '') or result.get('model_url', '')
                cover_url = result.get('cover_url', '') or result.get('preview_url', '')
                
                # Check if we got a valid model URL
                if model_url:
                    logger.info("✅ GENERATION COMPLETED! Model and cover URLs ready.")
                    logger.info(f"Model URL: {model_url}")
                    logger.info(f"Cover URL: {cover_url}")
                    return (model_url, cover_url, task_id)
                else:
                    # Task completed but no URL - log the full result for debugging
                    logger.error(f"❌ GENERATION COMPLETED but no model URL found. Full result: {result}")
                    return ("❌ GENERATION COMPLETED but no model URL returned", "", task_id)
            else:
                # Check both 'state' and 'status' fields for error reporting
                actual_status = result.get('state', result.get('status', 'unknown'))
                error_msg = result.get('error', f"Task status: {actual_status}")
                logger.error(f"❌ GENERATION FAILED: {error_msg}")
                logger.error(f"Full result for debugging: {result}")
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
            },
            "optional": {
                "output_directory": ("STRING", {"default": "hitem3d"}),
                "compress_large_files": ("BOOLEAN", {"default": True}),
                "max_file_size_mb": ("INT", {"default": 50, "min": 10, "max": 500, "step": 10}),
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
            # Check if runtime config should override file config
            if HiTem3DConfigNode.should_override_config():
                runtime_config = HiTem3DConfigNode.get_runtime_config()
                if runtime_config:
                    from hitem3d_comfyui.client import HiTem3DClient
                    self.client = HiTem3DClient(
                        access_key=runtime_config["access_key"],
                        secret_key=runtime_config["secret_key"],
                        api_base_url=runtime_config["api_base_url"]
                    )
                    logger.info("HiTem3D client loaded from runtime configuration (override enabled)")
                    return
            
            # First try runtime config from ConfigNode (if not overriding)
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
    
    def download_model(self,
                         model_url: str,
                         file_name: str = "model",
                         output_directory: str = "hitem3d",
                         compress_large_files: bool = True,
                         max_file_size_mb: int = 50) -> Tuple[str, str]:
        """
        Download 3D model from provided URL to ComfyUI output directory
        
        Returns:
            Tuple containing (model_path, status)
        """
        try:
            import os
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
            
            # Use ComfyUI output directory
            import folder_paths
            output_base = folder_paths.get_output_directory()
            output_dir = Path(output_base) / output_directory
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_path = output_dir / filename
            
            # Download the model using simple HTTP request
            import requests
            logger.info(f"Downloading model from: {model_url}")
            
            response = requests.get(model_url, stream=True)
            response.raise_for_status()
            
            # Get file size from headers if available
            content_length = response.headers.get('content-length')
            if content_length:
                file_size_mb = int(content_length) / (1024 * 1024)
                logger.info(f"Downloading file size: {file_size_mb:.2f} MB")
                
                # Check if file is very large
                if file_size_mb > max_file_size_mb:
                    logger.warning(f"Large file detected ({file_size_mb:.2f} MB > {max_file_size_mb} MB)")
                    
                    if compress_large_files:
                        return self._download_and_compress(response, output_path, file_size_mb, filename)
                    else:
                        logger.info("Proceeding with large file download (compression disabled)")
            
            # Standard download
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Check final file size
            final_size_mb = os.path.getsize(output_path) / (1024 * 1024)
            
            logger.info(f"Model downloaded to: {output_path}")
            logger.info(f"Final file size: {final_size_mb:.2f} MB")
            
            # Add size info to status
            if final_size_mb > 100:
                status = f"Downloaded successfully - Very Large File ({final_size_mb:.2f} MB)"
            elif final_size_mb > 25:
                status = f"Downloaded successfully - Large File ({final_size_mb:.2f} MB)"
            else:
                status = f"Downloaded successfully ({final_size_mb:.2f} MB)"
            
            return (str(output_path), status)
            
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
    
    def _download_and_compress(self, response, output_path, file_size_mb, filename):
        """Download large file and optionally compress it"""
        import os
        import gzip
        import shutil
        from pathlib import Path
        
        try:
            logger.info(f"Downloading and handling large file ({file_size_mb:.2f} MB)...")
            
            # Download to temporary location first
            temp_path = output_path.with_suffix(output_path.suffix + '.tmp')
            
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Check if we should compress
            actual_size_mb = os.path.getsize(temp_path) / (1024 * 1024)
            
            if actual_size_mb > 100:  # Very large files
                # Create compressed version
                compressed_path = output_path.with_suffix('.gz')
                
                logger.info(f"Compressing very large file ({actual_size_mb:.2f} MB)...")
                
                with open(temp_path, 'rb') as f_in:
                    with gzip.open(compressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                compressed_size_mb = os.path.getsize(compressed_path) / (1024 * 1024)
                compression_ratio = (1 - compressed_size_mb / actual_size_mb) * 100
                
                # Move original to final location
                shutil.move(temp_path, output_path)
                
                logger.info(f"Compression complete:")
                logger.info(f"  Original: {actual_size_mb:.2f} MB")
                logger.info(f"  Compressed: {compressed_size_mb:.2f} MB ({compression_ratio:.1f}% reduction)")
                
                status = f"Downloaded with compression - Original: {actual_size_mb:.2f} MB, Compressed: {compressed_size_mb:.2f} MB"
                
                # Return info about both files
                return (f"{output_path}|{compressed_path}", status)
            
            else:
                # Just move the file
                shutil.move(temp_path, output_path)
                status = f"Downloaded successfully - Large File ({actual_size_mb:.2f} MB)"
                return (str(output_path), status)
                
        except Exception as e:
            # Clean up temp file if it exists
            if temp_path.exists():
                temp_path.unlink()
            raise e


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
                "override_config": ("BOOLEAN", {"default": False}),
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
                     save_config: bool = False,
                     override_config: bool = False) -> Tuple[str, str]:
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
            HiTem3DConfigNode._runtime_config["override_config"] = override_config
            
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
    
    @classmethod
    def should_override_config(cls):
        """Check if runtime config should override file config"""
        return cls._runtime_config and cls._runtime_config.get("override_config", False)


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
                "height": ("INT", {"default": 512, "min": 256, "max": 2048, "step": 64}),
                "background_color": (["#000000", "#FFFFFF", "#808080", "#f0f0f0"], {"default": "#808080"}),
                "auto_rotate": ("BOOLEAN", {"default": True}),
                "show_wireframe": ("BOOLEAN", {"default": False}),
                "show_grid": ("BOOLEAN", {"default": True}),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("preview_html", "preview_file_path", "preview_url")
    FUNCTION = "preview_3d_model"
    CATEGORY = "HiTem3D"
    OUTPUT_NODE = True
    
    def preview_3d_model(self, model_path, width=512, height=512, background_color="#808080", 
                         auto_rotate=True, show_wireframe=False, show_grid=True):
        """Generate HTML preview of 3D model"""
        try:
            import os
            import base64
            from pathlib import Path
            
            if not model_path or not os.path.exists(model_path):
                error_html = self._create_error_preview("Model file not found", width, height)
                return (error_html, "❌ No preview file - model not found", "")
            
            # Get file extension to determine model type
            file_ext = Path(model_path).suffix.lower()
            supported_formats = ['.obj', '.glb', '.gltf', '.stl', '.fbx']
            
            if file_ext not in supported_formats:
                error_html = self._create_error_preview(f"Unsupported format: {file_ext}", width, height)
                return (error_html, "❌ No preview file - unsupported format", "")
            
            # Check file size and determine best handling approach
            file_size = os.path.getsize(model_path)
            file_size_mb = file_size / (1024 * 1024)
            
            # Multi-tier handling based on file size
            if file_size_mb > 100:  # Very large files (>100MB)
                preview_html = self._create_very_large_file_preview(model_path, file_size_mb, width, height)
                preview_file_path = self._save_preview_to_file(preview_html, model_path, "very_large")
                preview_url = self._get_file_url(preview_file_path)
                return (preview_html, preview_file_path, preview_url)
            elif file_size_mb > 25:  # Large files (25-100MB)
                preview_html = self._create_large_file_preview(model_path, file_size_mb, width, height)
                preview_file_path = self._save_preview_to_file(preview_html, model_path, "large")
                preview_url = self._get_file_url(preview_file_path)
                return (preview_html, preview_file_path, preview_url)
            elif file_size_mb > 10:  # Medium files (10-25MB) - try optimized preview
                preview_html = self._create_optimized_preview(model_path, file_size_mb, file_ext, width, height)
                preview_file_path = self._save_preview_to_file(preview_html, model_path, "optimized")
                preview_url = self._get_file_url(preview_file_path)
                return (preview_html, preview_file_path, preview_url)
            
            # For smaller files, try the full preview
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
                
                preview_file_path = self._save_preview_to_file(html_preview, model_path, "interactive")
                preview_url = self._get_file_url(preview_file_path)
                return (html_preview, preview_file_path, preview_url)
                
            except Exception as e:
                error_html = self._create_error_preview(f"Error reading model: {str(e)}", width, height)
                return (error_html, "❌ No preview file - error reading model", "")
                
        except Exception as e:
            logger.error(f"3D Preview Error: {e}")
            error_html = self._create_error_preview(f"Preview error: {str(e)}", width, height)
            return (error_html, "❌ No preview file - preview error", "")
    
    def _save_preview_to_file(self, html_content, model_path, preview_type):
        """Save the HTML preview to a file and return the file path"""
        try:
            from pathlib import Path
            import datetime
            
            # Create preview filename based on model file
            model_name = Path(model_path).stem
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            preview_filename = f"{model_name}_{preview_type}_preview_{timestamp}.html"
            
            # Use ComfyUI output directory
            output_base = folder_paths.get_output_directory()
            preview_dir = Path(output_base) / "hitem3d" / "previews"
            preview_dir.mkdir(parents=True, exist_ok=True)
            
            preview_file_path = preview_dir / preview_filename
            
            # Save HTML content
            with open(preview_file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"✅ Preview saved to: {preview_file_path}")
            
            # Return the file path as a clickable message
            return f"🌐 Preview saved: {preview_file_path}"
            
        except Exception as e:
            logger.error(f"Failed to save preview file: {e}")
            return f"❌ Failed to save preview: {str(e)}"
    
    def _get_file_url(self, file_path_message):
        """Extract file path from message and convert to file:// URL"""
        try:
            if file_path_message.startswith("🌐 Preview saved: "):
                file_path = file_path_message.replace("🌐 Preview saved: ", "")
                # Convert to file URL for browser opening
                file_url = f"file:///{file_path.replace(chr(92), '/')}"
                return file_url
            else:
                return ""
        except Exception as e:
            logger.error(f"Failed to create file URL: {e}")
            return ""
    
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
    
    def _create_optimized_preview(self, model_path, file_size_mb, file_ext, width, height):
        """Create optimized preview for medium-large files (10-25MB) with modern UI"""
        from pathlib import Path
        
        file_name = Path(model_path).name
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HiTem3D Model Preview - {file_name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            color: #f8fafc;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}
        
        .container {{
            width: {width}px;
            max-width: 90vw;
            background: rgba(30, 41, 59, 0.8);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            border: 1px solid rgba(148, 163, 184, 0.1);
            overflow: hidden;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        }}
        
        .header {{
            background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
            padding: 25px;
            text-align: center;
            position: relative;
        }}
        
        .header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="0.5"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)"/></svg>');
            opacity: 0.3;
        }}
        
        .header h1 {{
            font-size: 24px;
            font-weight: 700;
            color: white;
            margin-bottom: 8px;
            position: relative;
            z-index: 1;
        }}
        
        .header .subtitle {{
            color: rgba(255, 255, 255, 0.9);
            font-size: 14px;
            position: relative;
            z-index: 1;
        }}
        
        .content {{
            padding: 30px;
        }}
        
        .file-card {{
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(37, 99, 235, 0.05) 100%);
            border: 1px solid rgba(59, 130, 246, 0.2);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 25px;
            position: relative;
            overflow: hidden;
        }}
        
        .file-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #3b82f6, #8b5cf6, #06b6d4);
        }}
        
        .file-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-top: 16px;
        }}
        
        .file-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
        }}
        
        .file-item .icon {{
            font-size: 18px;
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: rgba(59, 130, 246, 0.2);
            border-radius: 8px;
        }}
        
        .file-item .label {{
            color: #94a3b8;
            font-weight: 500;
        }}
        
        .file-item .value {{
            color: #f1f5f9;
            font-weight: 600;
        }}
        
        .actions-section {{
            background: rgba(15, 23, 42, 0.6);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 25px;
        }}
        
        .actions-title {{
            color: #10b981;
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .actions-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 12px;
        }}
        
        .action-btn {{
            background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
            color: white;
            border: none;
            padding: 12px 16px;
            border-radius: 12px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            min-height: 48px;
        }}
        
        .action-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(245, 158, 11, 0.4);
            background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
        }}
        
        .action-btn:active {{
            transform: translateY(0);
        }}
        
        .performance-tip {{
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.05) 100%);
            border: 1px solid rgba(16, 185, 129, 0.2);
            border-radius: 12px;
            padding: 20px;
            margin-top: 20px;
        }}
        
        .performance-tip .tip-header {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 12px;
            color: #10b981;
            font-weight: 600;
        }}
        
        .performance-tip p {{
            color: #cbd5e1;
            line-height: 1.6;
            font-size: 14px;
        }}
        
        .footer {{
            background: rgba(15, 23, 42, 0.8);
            padding: 20px;
            text-align: center;
            color: #64748b;
            font-size: 12px;
        }}
        
        .footer a {{
            color: #f59e0b;
            text-decoration: none;
            font-weight: 500;
        }}
        
        .footer a:hover {{
            color: #fbbf24;
        }}
        
        @keyframes fadeInUp {{
            from {{
                opacity: 0;
                transform: translateY(20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        .container {{
            animation: fadeInUp 0.6s ease-out;
        }}
        
        @media (max-width: 768px) {{
            .container {{
                width: 100%;
                margin: 10px;
            }}
            
            .file-grid {{
                grid-template-columns: 1fr;
            }}
            
            .actions-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚡ HiTem3D Model Preview</h1>
            <p class="subtitle">Professional 3D Model Management</p>
        </div>
        
        <div class="content">
            <div class="file-card">
                <h3 style="color: #3b82f6; font-size: 20px; margin-bottom: 16px; display: flex; align-items: center; gap: 8px;">
                    📊 Model Information
                </h3>
                
                <div class="file-grid">
                    <div class="file-item">
                        <div class="icon">📄</div>
                        <div>
                            <div class="label">File Name</div>
                            <div class="value">{file_name}</div>
                        </div>
                    </div>
                    
                    <div class="file-item">
                        <div class="icon">🏷️</div>
                        <div>
                            <div class="label">Format</div>
                            <div class="value">{file_ext.upper()}</div>
                        </div>
                    </div>
                    
                    <div class="file-item">
                        <div class="icon">📏</div>
                        <div>
                            <div class="label">File Size</div>
                            <div class="value">{file_size_mb:.2f} MB</div>
                        </div>
                    </div>
                    
                    <div class="file-item">
                        <div class="icon">✅</div>
                        <div>
                            <div class="label">Status</div>
                            <div class="value">Ready</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="actions-section">
                <h3 class="actions-title">
                    � Quick Actions
                </h3>
                
                <div class="actions-grid">
                    <button class="action-btn" onclick="openInBlender()">
                        🔷 Blender
                    </button>
                    
                    <button class="action-btn" onclick="openInMeshLab()">
                        🔶 MeshLab
                    </button>
                    
                    <button class="action-btn" onclick="openIn3DViewer()">
                        👁️ 3D Viewer
                    </button>
                    
                    <button class="action-btn" onclick="copyPath()">
                        📋 Copy Path
                    </button>
                    
                    <button class="action-btn" onclick="openFolder()">
                        📁 Open Folder
                    </button>
                    
                    <button class="action-btn" onclick="showFileInfo()">
                        ℹ️ File Info
                    </button>
                </div>
            </div>
            
            <div class="performance-tip">
                <div class="tip-header">
                    💡 Optimization Insights
                </div>
                <p>
                    This {file_size_mb:.2f} MB model is optimized for professional 3D applications. 
                    For best performance, use dedicated software like Blender or MeshLab. 
                    The file size strikes a good balance between detail and performance.
                </p>
            </div>
        </div>
        
        <div class="footer">
            Created with ❤️ by <a href="https://www.geekatplay.com" target="_blank">Geekatplay Studio</a> | 
            Powered by <a href="https://www.hitem3d.ai" target="_blank">HiTem3D</a>
        </div>
    </div>
    
    <script>
        const modelPath = '{model_path.replace(chr(92), chr(92)+chr(92))}';
        const fileInfo = {{
            name: '{file_name}',
            format: '{file_ext.upper()}',
            size: '{file_size_mb:.2f} MB',
            path: modelPath
        }};
        
        // Add smooth animations
        document.addEventListener('DOMContentLoaded', function() {{
            const cards = document.querySelectorAll('.file-card, .actions-section, .performance-tip');
            cards.forEach((card, index) => {{
                card.style.animationDelay = `${{index * 0.1}}s`;
                card.style.animation = 'fadeInUp 0.6s ease-out forwards';
            }});
        }});
        
        function openInBlender() {{
            showNotification('🔷 Blender Instructions', 
                `To open in Blender:\\n\\n` +
                `1. Launch Blender\\n` +
                `2. File > Import > {file_ext.upper()}\\n` +
                `3. Navigate to: ${{modelPath}}\\n\\n` +
                `Tip: Use Edit > Preferences > Add-ons to enable STL import if needed.`
            );
        }}
        
        function openInMeshLab() {{
            showNotification('🔶 MeshLab Instructions',
                `To open in MeshLab:\\n\\n` +
                `1. Launch MeshLab\\n` +
                `2. File > Import Mesh\\n` +
                `3. Navigate to: ${{modelPath}}\\n\\n` +
                `Tip: MeshLab is excellent for mesh analysis and repair.`
            );
        }}
        
        function openIn3DViewer() {{
            showNotification('👁️ Windows 3D Viewer',
                `To open in 3D Viewer:\\n\\n` +
                `1. Right-click the file in Windows Explorer\\n` +
                `2. Select "Open with > 3D Viewer"\\n` +
                `3. Or drag the file to 3D Viewer\\n\\n` +
                `Path: ${{modelPath}}`
            );
        }}
        
        function copyPath() {{
            if (navigator.clipboard) {{
                navigator.clipboard.writeText(modelPath).then(() => {{
                    showNotification('📋 Success', 'File path copied to clipboard!', 'success');
                }}).catch(() => {{
                    fallbackCopyPath();
                }});
            }} else {{
                fallbackCopyPath();
            }}
        }}
        
        function fallbackCopyPath() {{
            const textArea = document.createElement('textarea');
            textArea.value = modelPath;
            document.body.appendChild(textArea);
            textArea.select();
            try {{
                document.execCommand('copy');
                showNotification('📋 Success', 'File path copied to clipboard!', 'success');
            }} catch (err) {{
                prompt('Copy this path:', modelPath);
            }}
            document.body.removeChild(textArea);
        }}
        
        function openFolder() {{
            const folderPath = modelPath.replace(/[^\\\\]*$/, '');
            showNotification('📁 Open Folder',
                `To open the containing folder:\\n\\n` +
                `Press Win+R and paste:\\n${{folderPath}}\\n\\n` +
                `Or use Windows Explorer to navigate to the folder.`
            );
        }}
        
        function showFileInfo() {{
            const info = 
                `📊 Detailed File Information:\\n\\n` +
                `Name: ${{fileInfo.name}}\\n` +
                `Format: ${{fileInfo.format}}\\n` +
                `Size: ${{fileInfo.size}}\\n` +
                `Path: ${{fileInfo.path}}\\n\\n` +
                `🎯 Recommendations:\\n` +
                `• Best for: Professional 3D editing\\n` +
                `• Compatible with: Most 3D software\\n` +
                `• Performance: Good balance of detail/size`;
            
            showNotification('ℹ️ File Information', info);
        }}
        
        function showNotification(title, message, type = 'info') {{
            // Create modern notification
            const notification = document.createElement('div');
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
                color: white;
                padding: 20px;
                border-radius: 12px;
                border: 1px solid rgba(148, 163, 184, 0.2);
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
                max-width: 400px;
                z-index: 1000;
                font-family: inherit;
                animation: slideIn 0.3s ease-out;
            `;
            
            notification.innerHTML = `
                <div style="font-weight: 600; margin-bottom: 8px; color: #f59e0b;">${{title}}</div>
                <div style="white-space: pre-line; font-size: 14px; line-height: 1.5;">${{message}}</div>
                <button onclick="this.parentElement.remove()" style="
                    position: absolute;
                    top: 8px;
                    right: 8px;
                    background: none;
                    border: none;
                    color: #94a3b8;
                    cursor: pointer;
                    font-size: 18px;
                ">×</button>
            `;
            
            document.body.appendChild(notification);
            
            // Auto remove after 5 seconds
            setTimeout(() => {{
                if (notification.parentElement) {{
                    notification.remove();
                }}
            }}, 5000);
        }}
        
        // Add CSS for slide in animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {{
                from {{
                    transform: translateX(100%);
                    opacity: 0;
                }}
                to {{
                    transform: translateX(0);
                    opacity: 1;
                }}
            }}
        `;
        document.head.appendChild(style);
    </script>
</body>
</html>"""

    def _create_very_large_file_preview(self, model_path, file_size_mb, width, height):
        """Create specialized preview for very large files (>100MB)"""
        from pathlib import Path
        
        file_name = Path(model_path).name
        file_ext = Path(model_path).suffix.lower()
        
        # Calculate some useful metrics
        estimated_vertices = int(file_size_mb * 50000)  # Rough estimate
        recommended_ram = max(8, int(file_size_mb * 4))  # Recommended RAM
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>HiTem3D Very Large File Manager</title>
    <style>
        body {{ 
            margin: 0; 
            padding: 20px; 
            background: #2d1b69; 
            color: white; 
            font-family: Arial, sans-serif;
        }}
        .container {{ 
            width: {width}px; 
            height: {height}px; 
            border: 2px solid #E91E63;
            border-radius: 8px;
            background: #1a1a2e;
            margin: 0 auto;
            padding: 20px;
            box-sizing: border-box;
            overflow-y: auto;
        }}
        .header {{
            text-align: center;
            margin-bottom: 20px;
        }}
        .file-icon {{
            font-size: 42px;
            margin-bottom: 10px;
        }}
        .file-info {{
            background: rgba(233, 30, 99, 0.1);
            padding: 12px;
            border-radius: 8px;
            margin: 10px 0;
            border-left: 4px solid #E91E63;
        }}
        .file-info h3 {{
            color: #E91E63;
            margin: 0 0 8px 0;
            font-size: 16px;
        }}
        .detail {{
            margin: 3px 0;
            font-size: 12px;
        }}
        .warning-section {{
            background: rgba(244, 67, 54, 0.15);
            border: 1px solid #F44336;
            padding: 12px;
            border-radius: 6px;
            margin: 10px 0;
        }}
        .recommendation-section {{
            background: rgba(76, 175, 80, 0.1);
            border: 1px solid #4CAF50;
            padding: 12px;
            border-radius: 6px;
            margin: 10px 0;
        }}
        .action-buttons {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin: 10px 0;
        }}
        .action-btn {{
            background: #E91E63;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 11px;
            flex: 1;
            min-width: 120px;
        }}
        .action-btn:hover {{
            background: #C2185B;
        }}
        .secondary-btn {{
            background: #607D8B;
        }}
        .secondary-btn:hover {{
            background: #546E7A;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="file-icon">🚀</div>
            <h2 style="color: #E91E63; margin: 0;">Very Large 3D Model</h2>
        </div>
        
        <div class="file-info">
            <h3>📊 File Statistics</h3>
            <div class="detail"><strong>File:</strong> {file_name}</div>
            <div class="detail"><strong>Format:</strong> {file_ext.upper()}</div>
            <div class="detail"><strong>Size:</strong> {file_size_mb:.2f} MB</div>
            <div class="detail"><strong>Est. Vertices:</strong> ~{estimated_vertices:,}</div>
            <div class="detail"><strong>Recommended RAM:</strong> {recommended_ram}+ GB</div>
        </div>
        
        <div class="warning-section">
            <h4 style="color: #FF5722; margin: 0 0 8px 0;">⚠️ Large File Warnings</h4>
            <div style="font-size: 11px;">
                • File is very large ({file_size_mb:.2f} MB) - not suitable for web preview<br>
                • May require high-end hardware for smooth editing<br>
                • Loading times may be significant in 3D applications<br>
                • Consider model optimization for better performance
            </div>
        </div>
        
        <div class="recommendation-section">
            <h4 style="color: #4CAF50; margin: 0 0 8px 0;">💡 Professional Recommendations</h4>
            <div style="font-size: 11px;">
                • <strong>Blender:</strong> Best for high-poly editing and optimization<br>
                • <strong>MeshLab:</strong> Excellent for mesh analysis and simplification<br>
                • <strong>CloudCompare:</strong> For point cloud and scientific analysis<br>
                • <strong>Autodesk Fusion:</strong> For CAD and engineering workflows
            </div>
        </div>
        
        <div class="action-buttons">
            <button class="action-btn" onclick="openAdvancedOptions()">
                🔧 Advanced Tools
            </button>
            <button class="action-btn secondary-btn" onclick="copyPath()">
                📋 Copy Path
            </button>
            <button class="action-btn secondary-btn" onclick="showOptimization()">
                ⚡ Optimization Tips
            </button>
            <button class="action-btn secondary-btn" onclick="openFolder()">
                📁 Open Folder
            </button>
        </div>
        
        <div style="margin-top: 15px; padding: 10px; background: rgba(0,0,0,0.3); border-radius: 4px; font-size: 10px;">
            <strong>📍 File Location:</strong><br>
            <code style="color: #E91E63; word-break: break-all;">{model_path}</code>
        </div>
    </div>
    
    <script>
        const modelPath = '{model_path}';
        const fileSize = {file_size_mb:.2f};
        
        function openAdvancedOptions() {{
            const message = `Advanced 3D Applications for Large Files:
            
🔷 BLENDER (Recommended)
   • Best for: High-poly editing, animation, rendering
   • Memory: Use {recommended_ram}+ GB RAM
   • Tip: Enable "Limit Selection to Visible" for performance
   
🔶 MESHLABI
   • Best for: Mesh analysis, simplification, repair
   • Tip: Use "Quadric Edge Collapse Decimation" to reduce poly count
   
⚙️ CLOUDCOMPARE
   • Best for: Point clouds, scientific analysis
   • Great for: Large mesh statistics and measurements
   
🎯 AUTODESK FUSION 360
   • Best for: CAD workflows, engineering analysis
   • Tip: Import as mesh for visualization, convert for editing`;
            
            alert(message);
        }}
        
        function showOptimization() {{
            const message = `Optimization Strategies for {file_size_mb:.2f} MB Model:
            
📉 REDUCE POLYGON COUNT:
   • MeshLab: Filters > Remeshing > Quadric Edge Collapse
   • Blender: Modifier > Decimate > Ratio: 0.1-0.5
   
🎯 LEVEL OF DETAIL (LOD):
   • Create multiple versions: High, Medium, Low detail
   • Use appropriate version for specific tasks
   
💾 FILE FORMAT OPTIMIZATION:
   • GLB: Best compression for complex models
   • OBJ: Good compatibility, larger file size
   • STL: Simple format, good for 3D printing
   
⚡ PERFORMANCE TIPS:
   • Close other applications when working
   • Use SSD storage for faster loading
   • Consider cloud-based 3D processing`;
            
            alert(message);
        }}
        
        function copyPath() {{
            if (navigator.clipboard) {{
                navigator.clipboard.writeText(modelPath).then(() => {{
                    alert('✅ File path copied to clipboard!');
                }}).catch(() => {{
                    prompt('Copy this path:', modelPath);
                }});
            }} else {{
                prompt('Copy this path:', modelPath);
            }}
        }}
        
        function openFolder() {{
            alert('📁 To open containing folder:\\n\\n1. Open Windows Explorer (Win+E)\\n2. Navigate to:\\n' + modelPath.replace(/[^\\\\]*$/, ''));
        }}
    </script>
    
    <div style="position: fixed; bottom: 5px; right: 10px; font-size: 9px; opacity: 0.5;">
        HiTem3D Large File Manager v2.0
    </div>
</body>
</html>"""

    def _create_large_file_preview(self, model_path, file_size_mb, width, height):
        """Create preview for large model files without embedding the data"""
        from pathlib import Path
        
        file_name = Path(model_path).name
        file_ext = Path(model_path).suffix.lower()
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>HiTem3D Large File Preview</title>
    <style>
        body {{ 
            margin: 0; 
            padding: 20px; 
            background: #404040; 
            color: white; 
            font-family: Arial, sans-serif;
        }}
        .container {{ 
            width: {width}px; 
            height: {height}px; 
            border: 2px solid #4CAF50;
            border-radius: 8px;
            background: #2a2a2a;
            margin: 0 auto;
            padding: 20px;
            box-sizing: border-box;
        }}
        .info-content {{
            text-align: center;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}
        .file-icon {{
            font-size: 64px;
            margin-bottom: 15px;
        }}
        .file-info {{
            background: rgba(76, 175, 80, 0.1);
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }}
        .file-info h3 {{
            color: #4CAF50;
            margin: 0 0 10px 0;
        }}
        .detail {{
            margin: 5px 0;
            font-size: 14px;
        }}
        .note {{
            background: rgba(255, 193, 7, 0.1);
            color: #FFC107;
            padding: 10px;
            border-radius: 4px;
            margin-top: 15px;
            font-size: 12px;
        }}
        .credit {{
            position: absolute;
            bottom: 10px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 10px;
            opacity: 0.7;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="info-content">
            <div class="file-icon">📦</div>
            
            <div class="file-info">
                <h3>3D Model File Ready</h3>
                <div class="detail"><strong>File:</strong> {file_name}</div>
                <div class="detail"><strong>Format:</strong> {file_ext.upper()}</div>
                <div class="detail"><strong>Size:</strong> {file_size_mb:.2f} MB</div>
                <div class="detail"><strong>Path:</strong> {model_path}</div>
            </div>
            
            <div class="note">
                ⚠️ <strong>Large File Notice:</strong><br>
                This file is too large ({file_size_mb:.2f} MB) for embedded preview.<br>
                The model has been successfully downloaded and is ready for use in other applications.<br><br>
                
                <strong>You can open this file with:</strong><br>
                • Blender<br>
                • MeshLab<br>
                • 3D Viewer (Windows)<br>
                • Any CAD software
            </div>
        </div>
    </div>
    
    <div class="credit">
        Created by: Geekatplay Studio by Vladimir Chopine | 
        <a href="https://www.geekatplay.com" style="color: #4CAF50;">www.geekatplay.com</a>
    </div>
</body>
</html>"""

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


class HTMLPreviewer:
    """
    HTML Previewer Node for ComfyUI
    
    Inputs:
      - base_dir (optional, text): Base directory for HTML files
      - file_name (optional, text): Name of HTML file to preview
      - absolute_path (optional, text): Absolute path to HTML file (takes precedence)
      - auto_refresh_token (optional): Any changing value to force frontend refresh
      - html_content (optional): Raw HTML content to display
    Output:
      - preview_url (string): /html_previewer/open?path=...
    """
    
    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {},
            "optional": {
                "base_dir": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "Base directory path (optional)"
                }),
                "file_name": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "HTML filename (optional)"
                }),
                "absolute_path": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "Full path to HTML file"
                }),
                "auto_refresh_token": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "Change this to refresh preview"
                }),
                "html_content": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "Raw HTML content (will be saved to temp file)"
                }),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("preview_url",)
    FUNCTION = "make_url"
    CATEGORY = "HiTem3D/Preview"

    def make_url(self, base_dir: str = "", file_name: str = "", absolute_path: str = "", 
                 auto_refresh_token: str = "", html_content: str = ""):
        """Generate preview URL for HTML content"""
        
        if not HTML_PREVIEWER_AVAILABLE:
            return ("HTML Previewer not available - missing server imports",)
        
        # If html_content is provided, save it to a temp file
        if html_content.strip():
            try:
                # Create a unique filename for this HTML content
                import hashlib
                content_hash = hashlib.md5(html_content.encode()).hexdigest()[:8]
                temp_filename = f"preview_{content_hash}_{int(time.time())}.html"
                temp_path = TEMP_DIR / temp_filename
                
                # Save HTML content to temp file
                with open(temp_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                # Use the temp file path
                absolute_path = str(temp_path)
                logger.info(f"HTML Previewer: Saved content to {absolute_path}")
                
            except Exception as e:
                logger.error(f"HTML Previewer: Error saving HTML content: {e}")
                return (f"Error saving HTML content: {e}",)
        
        # Build URL but do NOT validate here (validation is at request time)
        if absolute_path:
            path_q = urllib.parse.quote(absolute_path)
            url = f"/html_previewer/open?path={path_q}"
        else:
            base_q = urllib.parse.quote(base_dir)
            file_q = urllib.parse.quote(file_name or DEFAULT_INDEX)
            url = f"/html_previewer/open?base={base_q}&file={file_q}"

        # Append a token to force UI reload if needed
        if auto_refresh_token:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}t={urllib.parse.quote(auto_refresh_token)}"

        logger.info(f"HTML Previewer: Generated URL: {url}")
        return (url,)


class DynamicValueGenerator:
    """
    Dynamic Value Generator Node for ComfyUI
    
    Generates dynamic values for auto-refresh tokens and other changing content.
    Perfect for triggering HTML preview refreshes and dynamic content updates.
    """
    
    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {
                "value_type": (["timestamp", "counter", "uuid", "random", "custom"], {
                    "default": "timestamp"
                }),
            },
            "optional": {
                "custom_prefix": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "Custom prefix (optional)"
                }),
                "counter_start": ("INT", {
                    "default": 1,
                    "min": 0,
                    "max": 999999,
                    "step": 1
                }),
                "format_string": ("STRING", {
                    "default": "%Y%m%d_%H%M%S",
                    "multiline": False,
                    "placeholder": "Timestamp format (strftime)"
                }),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("dynamic_value",)
    FUNCTION = "generate_value"
    CATEGORY = "HiTem3D/Utils"

    def __init__(self):
        self.counter = 0

    def generate_value(self, value_type: str = "timestamp", custom_prefix: str = "", 
                      counter_start: int = 1, format_string: str = "%Y%m%d_%H%M%S"):
        """Generate dynamic values for auto-refresh and other purposes"""
        
        try:
            if value_type == "timestamp":
                # Generate timestamp string
                timestamp = datetime.datetime.now().strftime(format_string)
                value = f"{custom_prefix}{timestamp}" if custom_prefix else timestamp
                
            elif value_type == "counter":
                # Increment counter
                self.counter += 1
                if self.counter == 1:  # First run, start from specified value
                    self.counter = counter_start
                value = f"{custom_prefix}{self.counter}" if custom_prefix else str(self.counter)
                
            elif value_type == "uuid":
                # Generate UUID
                uuid_str = str(uuid.uuid4())[:8]  # Short UUID
                value = f"{custom_prefix}{uuid_str}" if custom_prefix else uuid_str
                
            elif value_type == "random":
                # Generate random number
                random_num = random.randint(1000, 9999)
                value = f"{custom_prefix}{random_num}" if custom_prefix else str(random_num)
                
            elif value_type == "custom":
                # Custom format with timestamp
                current_time = time.time()
                value = f"{custom_prefix}{int(current_time)}" if custom_prefix else str(int(current_time))
                
            else:
                # Fallback to timestamp
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                value = f"{custom_prefix}{timestamp}" if custom_prefix else timestamp
            
            logger.info(f"Dynamic Value Generator: Generated '{value}' (type: {value_type})")
            return (value,)
            
        except Exception as e:
            logger.error(f"Dynamic Value Generator: Error generating value: {e}")
            # Fallback to simple timestamp
            fallback = str(int(time.time()))
            return (fallback,)


class TextTemplate:
    """
    Text Template Node for ComfyUI
    
    Creates dynamic text content with placeholders and templates.
    Perfect for generating HTML content with dynamic values.
    """
    
    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {
                "template": ("STRING", {
                    "default": "Generated at: {{timestamp}}",
                    "multiline": True,
                    "placeholder": "Text template with {{placeholders}}"
                }),
            },
            "optional": {
                "value1": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "Value for {{value1}}"
                }),
                "value2": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "Value for {{value2}}"
                }),
                "value3": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "Value for {{value3}}"
                }),
                "timestamp_format": ("STRING", {
                    "default": "%Y-%m-%d %H:%M:%S",
                    "multiline": False,
                    "placeholder": "Timestamp format"
                }),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text_output",)
    FUNCTION = "process_template"
    CATEGORY = "HiTem3D/Utils"

    def process_template(self, template: str, value1: str = "", value2: str = "", value3: str = "", 
                        timestamp_format: str = "%Y-%m-%d %H:%M:%S"):
        """Process text template with dynamic values"""
        
        import datetime
        import time
        import re
        
        try:
            # Get current timestamp
            current_time = datetime.datetime.now()
            timestamp = current_time.strftime(timestamp_format)
            
            # Create replacement dictionary
            replacements = {
                "timestamp": timestamp,
                "time": timestamp,
                "date": current_time.strftime("%Y-%m-%d"),
                "datetime": timestamp,
                "unix": str(int(time.time())),
                "value1": value1,
                "value2": value2,
                "value3": value3,
                "year": current_time.strftime("%Y"),
                "month": current_time.strftime("%m"),
                "day": current_time.strftime("%d"),
                "hour": current_time.strftime("%H"),
                "minute": current_time.strftime("%M"),
                "second": current_time.strftime("%S"),
            }
            
            # Process template
            result = template
            for key, value in replacements.items():
                # Replace {{key}} patterns
                pattern = f"{{{{\\s*{key}\\s*}}}}"
                result = re.sub(pattern, str(value), result, flags=re.IGNORECASE)
            
            logger.info(f"Text Template: Processed template with {len(replacements)} variables")
            return (result,)
            
        except Exception as e:
            logger.error(f"Text Template: Error processing template: {e}")
            return (template,)  # Return original template on error


class HiTem3DHistoryNode:
    """History Node - Tracks all generated models and textures with clickable download links"""
    
    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {},
            "optional": {
                "model_url": ("STRING", {"default": ""}),
                "cover_url": ("STRING", {"default": ""}),
                "task_id": ("STRING", {"default": ""}),
                "model_name": ("STRING", {"default": ""}),
                "load_history": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("history_html", "history_status")
    FUNCTION = "update_history"
    CATEGORY = "HiTem3D"
    OUTPUT_NODE = True

    def __init__(self):
        # Use node folder for history.json
        self.history_file = CURRENT_DIR / "history.json"
        
    def update_history(self, model_url: str = "", cover_url: str = "", task_id: str = "", model_name: str = "", load_history: bool = False):
        """Update history file and display all entries"""
        
        # Always load current history first
        history = self._load_history()
        
        # If new URLs provided, append to history
        if model_url and cover_url and "❌" not in model_url and "❌" not in cover_url:
            # Add new entry at the beginning
            new_entry = {
                "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "model_url": model_url,
                "texture_url": cover_url,
                "task_id": task_id,
                "model_name": model_name
            }
            history.insert(0, new_entry)
            
            # Keep last 100 entries
            history = history[:100]
            
            # Save updated history
            self._save_history(history)
            logger.info(f"History: Added new entry. Total entries: {len(history)}")
        
        # If load_history is True or we have history entries, generate HTML display
        # This ensures history is always displayed when requested, even without new entries
        if load_history or history or (model_url and cover_url):
            history_html = self._generate_html_display(history)
            
            # Generate text display for node widget
            history_text = self._generate_text_display(history)
            
            # Generate status message
            if load_history:
                status = f"✅ History loaded manually - {len(history)} entries"
            elif model_url and cover_url:
                status = f"✅ History updated - {len(history)} entries"
            else:
                status = f"✅ History loaded - {len(history)} entries"
                
            if not history:
                status = "📦 No history yet - generate models to populate history"
            
            # Return both outputs with UI display
            return {"ui": {"text": [history_text]}, "result": (history_html, status)}
        
        # If no load_history flag and no new entries, return empty but indicate how to load
        history_html = self._generate_html_display([])
        history_text = "📦 History not loaded\n\nSet 'load_history' to True to display existing history,\nor provide model URLs to add new entries."
        status = "ℹ️ Set load_history=True to display history"
        
        return {"ui": {"text": [history_text]}, "result": (history_html, status)}
    
    def _generate_text_display(self, history: list) -> str:
        """Generate simple text display for node widget"""
        if not history:
            return "📦 No history yet\n\nGenerate models to see history here."
        
        lines = [f"📚 Generation History ({len(history)} items)\n" + "="*50 + "\n"]
        for i, entry in enumerate(history[:10], 1):  # Show only first 10 in node
            date = entry.get('date', 'Unknown')
            lines.append(f"#{i} - {date}")
            lines.append(f"   Model: {entry.get('model_url', 'N/A')[:60]}...")
            lines.append(f"   Texture: {entry.get('texture_url', 'N/A')[:60]}...")
            lines.append("")
        
        if len(history) > 10:
            lines.append(f"... and {len(history) - 10} more entries")
            lines.append(f"Connect history_html output to view all in browser")
        
        return "\n".join(lines)
    
    def _load_history(self) -> list:
        """Load history from JSON file"""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"History: Could not load history.json: {e}")
        return []
    
    def _save_history(self, history: list):
        """Save history to JSON file"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"History: Could not save history.json: {e}")
    
    def _generate_html_display(self, history: list) -> str:
        """Generate HTML display for browser viewing"""
        
        if not history:
            return "<html><body style='font-family:Arial;padding:20px;background:#2a2a2a;color:white;'><h2>📦 No history yet</h2><p>Generate models to see them here.</p></body></html>"
        
        # Build list
        items = ""
        for i, entry in enumerate(history, 1):
            # Use correct keys with fallbacks for backward compatibility
            date = entry.get('date', entry.get('time', 'Unknown'))
            model_url = entry.get('model_url', entry.get('model', ''))
            texture_url = entry.get('texture_url', entry.get('texture', ''))
            task_id = entry.get('task_id', '')
            model_name = entry.get('model_name', '')
            
            # Build info line
            info_parts = [f"#{i} - {date}"]
            if model_name:
                info_parts.append(f"Name: {model_name}")
            if task_id:
                info_parts.append(f"Task: {task_id}")
            info_line = " | ".join(info_parts)
            
            items += f"""
            <div style='background:{"#333" if i%2==0 else "#2a2a2a"};padding:15px;margin:5px 0;border-radius:8px;'>
                <div style='color:#4a9eff;font-weight:bold;margin-bottom:8px;'>{info_line}</div>
                <a href='{model_url}' target='_blank' style='display:inline-block;background:#4CAF50;color:white;padding:8px 15px;margin:5px 5px 5px 0;border-radius:5px;text-decoration:none;'>⬇️ Download Model</a>
                <a href='{texture_url}' target='_blank' style='display:inline-block;background:#2196F3;color:white;padding:8px 15px;margin:5px;border-radius:5px;text-decoration:none;'>�️ Download Texture</a>
            </div>
            """
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>HiTem3D History</title>
    <style>
        body {{ font-family: Arial; background: #1a1a1a; color: white; margin: 0; padding: 20px; }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        h1 {{ color: #4a9eff; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
        .history {{ max-height: 600px; overflow-y: auto; margin-top: 20px; }}
        .history::-webkit-scrollbar {{ width: 10px; }}
        .history::-webkit-scrollbar-track {{ background: #2a2a2a; }}
        .history::-webkit-scrollbar-thumb {{ background: #4a9eff; border-radius: 5px; }}
        a:hover {{ opacity: 0.8; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 HiTem3D Generation History ({len(history)} items)</h1>
        <div class="history">{items}</div>
    </div>
</body>
</html>
        """


# Node mappings for ComfyUI
NODE_CLASS_MAPPINGS = {
    "HiTem3DNode": HiTem3DNode,
    "HiTem3DDownloaderNode": HiTem3DDownloaderNode,
    "HiTem3DConfigNode": HiTem3DConfigNode,
    "HiTem3DPreviewNode": HiTem3DPreviewNode,
    "HTMLPreviewer": HTMLPreviewer,
    "DynamicValueGenerator": DynamicValueGenerator,
    "TextTemplate": TextTemplate,
    "HiTem3DHistoryNode": HiTem3DHistoryNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "HiTem3DNode": "🎯 HiTem3D Generator",
    "HiTem3DDownloaderNode": "⬇️ HiTem3D Downloader", 
    "HiTem3DConfigNode": "⚙️ HiTem3D Config",
    "HiTem3DPreviewNode": "👁️ HiTem3D 3D Preview",
    "HTMLPreviewer": "🌐 HTML Previewer (Local)",
    "DynamicValueGenerator": "🔄 Dynamic Value Generator",
    "TextTemplate": "📝 Text Template",
    "HiTem3DHistoryNode": "📚 HiTem3D History",
}