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
                "model": (["hitem3dv1", "hitem3dv1.5", "scene-portraitv1.5"], {"default": "hitem3dv1.5"}),
                "resolution": ([512, 1024, 1536, "1536pro"], {"default": 1024}),
                "output_format": (["obj", "glb", "stl", "fbx"], {"default": "glb"}),
                "generation_type": (["geometry_only", "texture_only", "both"], {"default": "both"}),
                "face_count": ("INT", {"default": 1000000, "min": 100000, "max": 2000000, "step": 10000}),
                "timeout": ("INT", {"default": 300, "min": 60, "max": 1800, "step": 30}),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("model_url", "cover_url", "task_id")
    FUNCTION = "generate_3d_model"
    CATEGORY = "HiTem3D"
    
    def __init__(self):
        self.client = None
        self._load_client()
    
    def _load_client(self):
        """Load HiTem3D API client from config"""
        try:
            if CONFIG_PATH.exists():
                self.client = create_client_from_config(str(CONFIG_PATH))
                logger.info("HiTem3D client loaded successfully")
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
                         timeout: int = 300) -> Tuple[str, str, str]:
        """
        Generate 3D model from input images
        
        Returns:
            Tuple of (model_url, cover_url, task_id)
        """
        try:
            if self.client is None:
                self._load_client()
            
            logger.info("Starting 3D model generation...")
            
            # Convert images to bytes
            front_bytes = tensor_to_image_bytes(front_image)
            back_bytes = tensor_to_image_bytes(back_image) if back_image is not None else None
            left_bytes = tensor_to_image_bytes(left_image) if left_image is not None else None
            right_bytes = tensor_to_image_bytes(right_image) if right_image is not None else None
            
            # Convert parameters
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
            logger.info("Waiting for completion...")
            
            # Wait for completion
            result = self.client.wait_for_completion(task_id, timeout=timeout)
            
            model_url = result.get('url', '')
            cover_url = result.get('cover_url', '')
            
            logger.info("3D model generation completed successfully!")
            logger.info(f"Model URL: {model_url}")
            logger.info(f"Cover URL: {cover_url}")
            
            return (model_url, cover_url, task_id)
            
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
    ComfyUI node for downloading 3D models from HiTem3D URLs
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_url": ("STRING", {"default": ""}),
                "filename": ("STRING", {"default": "model"}),
            },
            "optional": {
                "output_directory": ("STRING", {"default": "output/hitem3d"}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("file_path",)
    FUNCTION = "download_model"
    CATEGORY = "HiTem3D"
    OUTPUT_NODE = True
    
    def __init__(self):
        self.client = None
        self._load_client()
    
    def _load_client(self):
        """Load HiTem3D API client from config"""
        try:
            if CONFIG_PATH.exists():
                self.client = create_client_from_config(str(CONFIG_PATH))
                logger.info("HiTem3D client loaded successfully")
            else:
                logger.error(f"Config file not found: {CONFIG_PATH}")
                raise FileNotFoundError(f"Config file not found: {CONFIG_PATH}")
        except Exception as e:
            logger.error(f"Failed to load HiTem3D client: {str(e)}")
            raise
    
    def download_model(self, 
                      model_url: str,
                      filename: str = "model",
                      output_directory: str = "output/hitem3d") -> Tuple[str]:
        """
        Download 3D model from URL
        
        Returns:
            Tuple containing the local file path
        """
        try:
            if self.client is None:
                self._load_client()
            
            if not model_url or model_url.startswith("❌"):
                return (f"❌ DOWNLOAD FAILED: Invalid or error model URL: {model_url}",)
            
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
            
            # Create output path
            output_dir = Path(output_directory)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_path = output_dir / f"{filename}{extension}"
            
            # Download the model
            logger.info(f"Downloading model from: {model_url}")
            downloaded_path = self.client.download_model(model_url, str(output_path))
            
            logger.info(f"Model downloaded to: {downloaded_path}")
            return (downloaded_path,)
            
        except Exception as e:
            error_msg = str(e)
            if "Invalid or error model URL" in error_msg:
                error_msg = "❌ DOWNLOAD FAILED: No valid model URL provided. Check if 3D generation completed successfully."
            else:
                error_msg = f"❌ DOWNLOAD FAILED: {error_msg}"
            
            logger.error(error_msg)
            return (error_msg,)


class HiTem3DConfigNode:
    """
    ComfyUI node for configuring HiTem3D API credentials
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "access_key": ("STRING", {"default": ""}),
                "secret_key": ("STRING", {"default": ""}),
            },
            "optional": {
                "api_base_url": ("STRING", {"default": "https://api.hitem3d.ai"}),
                "save_config": ("BOOLEAN", {"default": True}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("status",)
    FUNCTION = "update_config"
    CATEGORY = "HiTem3D"
    OUTPUT_NODE = True
    
    def update_config(self, 
                     access_key: str,
                     secret_key: str,
                     api_base_url: str = "https://api.hitem3d.ai",
                     save_config: bool = True) -> Tuple[str]:
        """
        Update HiTem3D API configuration
        
        Returns:
            Tuple containing status message
        """
        try:
            if not access_key or not secret_key:
                return ("ERROR: Access key and secret key are required",)
            
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
            
            if save_config:
                with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4)
                
                logger.info("Configuration updated and saved")
                return ("Configuration updated and saved successfully",)
            else:
                logger.info("Configuration updated (not saved)")
                return ("Configuration updated (not saved to file)",)
                
        except Exception as e:
            error_msg = f"Failed to update configuration: {str(e)}"
            logger.error(error_msg)
            return (f"ERROR: {error_msg}",)


# Node mappings for ComfyUI
NODE_CLASS_MAPPINGS = {
    "HiTem3DNode": HiTem3DNode,
    "HiTem3DDownloaderNode": HiTem3DDownloaderNode,
    "HiTem3DConfigNode": HiTem3DConfigNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "HiTem3DNode": "HiTem3D Generator",
    "HiTem3DDownloaderNode": "HiTem3D Downloader", 
    "HiTem3DConfigNode": "HiTem3D Config",
}