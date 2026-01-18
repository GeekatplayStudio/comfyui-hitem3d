"""
HiTem3D API Client
Handles authentication and communication with HiTem3D API service

Created by: Geekatplay Studio by Vladimir Chopine
Website: www.geekatplay.com
Patreon: https://www.patreon.com/c/geekatplay
YouTube: @geekatplay and @geekatplay-ru

Get HiTem3D credits with referral code: https://www.hitem3d.ai/?sp_source=Geekatplay
"""

import requests
import json
import base64
import time
import logging
from typing import Optional, Dict, Any, Union, List
from pathlib import Path

logger = logging.getLogger(__name__)

class HiTem3DAPIClient:
    """Client for HiTem3D API communication"""
    
    def __init__(self, access_key: str, secret_key: str, base_url: str = "https://api.hitem3d.ai"):
        """
        Initialize HiTem3D API client
        
        Args:
            access_key: HiTem3D access key
            secret_key: HiTem3D secret key
            base_url: API base URL
        """
        self.access_key = access_key
        self.secret_key = secret_key
        self.base_url = base_url.rstrip('/')
        self.access_token = None
        self.token_expires_at = 0
        
    def _get_basic_auth_header(self) -> str:
        """Generate Basic auth header for token request"""
        credentials = f"{self.access_key}:{self.secret_key}"
        encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        return f"Basic {encoded_credentials}"
    
    def _get_token(self) -> str:
        """Get or refresh access token"""
        current_time = time.time()
        
        # Check if we have a valid token (24h validity with 1h buffer)
        if self.access_token and current_time < self.token_expires_at - 3600:
            return self.access_token
        
        # Request new token
        url = f"{self.base_url}/open-api/v1/auth/token"
        headers = {
            'Authorization': self._get_basic_auth_header(),
            'Content-Type': 'application/json',
            'Accept': '*/*'
        }
        
        try:
            response = requests.post(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if data.get('code') == 200:
                self.access_token = data['data']['accessToken']
                # Token valid for 24 hours
                self.token_expires_at = current_time + 24 * 3600
                logger.info("Successfully obtained access token")
                return self.access_token
            else:
                raise Exception(f"Token request failed: {data.get('msg', 'Unknown error')}")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get access token: {str(e)}")
    
    def create_task(self, 
                   front_image: bytes,
                   back_image: Optional[bytes] = None,
                   left_image: Optional[bytes] = None,
                   right_image: Optional[bytes] = None,
                   model: str = "hitem3dv1.5",
                   resolution: Union[int, str] = 1024,
                   face_count: int = 1000000,
                   output_format: int = 2,  # 1=obj, 2=glb, 3=stl, 4=fbx, 5=usdz
                   request_type: int = 3,   # 1=geometry, 2=texture, 3=both
                   callback_url: Optional[str] = None) -> str:
        """
        Create a 3D generation task
        
        Args:
            front_image: Required front view image bytes
            back_image: Optional back view image bytes
            left_image: Optional left side image bytes  
            right_image: Optional right side image bytes
            model: Model version (hitem3dv1, hitem3dv1.5, hitem3dv2.0, scene-portraitv1.5)
            resolution: Output resolution (512, 1024, 1536, 1536pro)
            face_count: Number of faces (100000-2000000)
            output_format: Output format (1=obj, 2=glb, 3=stl, 4=fbx, 5=usdz)
            request_type: Generation type (1=geometry, 2=texture, 3=both)
            callback_url: Optional callback URL
            
        Returns:
            Task ID string
        """
        token = self._get_token()
        url = f"{self.base_url}/open-api/v1/submit-task"
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': '*/*'
        }
        
        # Prepare form data
        data = {
            'request_type': str(request_type),
            'model': model,
            'resolution': str(resolution),
            'face': str(face_count),
            'format': str(output_format)
        }
        
        if callback_url:
            data['callback_url'] = callback_url
        
        # Prepare files for upload
        files = []
        
        # Check if we have multiple images (multi-view mode)
        multi_images = [img for img in [front_image, back_image, left_image, right_image] if img is not None]
        
        if len(multi_images) > 1:
            # Multi-view mode
            view_names = ['front', 'back', 'left', 'right']
            for i, img_bytes in enumerate([front_image, back_image, left_image, right_image]):
                if img_bytes is not None:
                    files.append(('multi_images', (f'{view_names[i]}.jpg', img_bytes, 'image/jpeg')))
        else:
            # Single image mode
            files.append(('images', ('front.jpg', front_image, 'image/jpeg')))
        
        try:
            response = requests.post(url, headers=headers, files=files, data=data, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            if result.get('code') == 200:
                task_id = result['data']['task_id']
                logger.info(f"Successfully created task: {task_id}")
                return task_id
            else:
                error_code = result.get('code', 'Unknown')
                error_msg = result.get('msg', 'Unknown error')
                
                # Translate common Chinese error messages
                if '余额不足' in error_msg or error_code == 30010000:
                    error_msg = "Insufficient balance - Please add credits to your HiTem3D account"
                elif 'balance is not enough' in error_msg.lower():
                    error_msg = "Insufficient balance - Please add credits to your HiTem3D account"
                
                raise Exception(f"Task creation failed (Code: {error_code}): {error_msg}")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to create task: {str(e)}")
        finally:
            # Close file objects
            for file_tuple in files:
                if hasattr(file_tuple[1][1], 'close'):
                    file_tuple[1][1].close()
    
    def query_task(self, task_id: str) -> Dict[str, Any]:
        """
        Query task status and results
        
        Args:
            task_id: Task ID to query
            
        Returns:
            Task status information
        """
        token = self._get_token()
        url = f"{self.base_url}/open-api/v1/query-task"
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': '*/*'
        }
        
        params = {'task_id': task_id}
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if result.get('code') == 200:
                return result['data']
            else:
                raise Exception(f"Task query failed: {result.get('msg', 'Unknown error')}")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to query task: {str(e)}")
    
    def wait_for_completion(self, task_id: str, timeout: int = 300, poll_interval: int = 10) -> Dict[str, Any]:
        """
        Wait for task completion with polling
        
        Args:
            task_id: Task ID to wait for
            timeout: Maximum time to wait in seconds
            poll_interval: Polling interval in seconds
            
        Returns:
            Final task result
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                result = self.query_task(task_id)
                state = result.get('state', '').lower()
                
                if state == 'success':
                    logger.info(f"Task {task_id} completed successfully")
                    return result
                elif state == 'failed':
                    raise Exception(f"Task {task_id} failed")
                elif state in ['created', 'queueing', 'processing']:
                    logger.info(f"Task {task_id} status: {state}")
                    time.sleep(poll_interval)
                else:
                    logger.warning(f"Unknown task state: {state}")
                    time.sleep(poll_interval)
                    
            except Exception as e:
                logger.error(f"Error polling task {task_id}: {str(e)}")
                time.sleep(poll_interval)
        
        raise Exception(f"Task {task_id} timeout after {timeout} seconds")
    
    def download_model(self, url: str, output_path: str) -> str:
        """
        Download 3D model from URL
        
        Args:
            url: Model download URL
            output_path: Local path to save the model
            
        Returns:
            Path to downloaded file
        """
        try:
            response = requests.get(url, timeout=120, stream=True)
            response.raise_for_status()
            
            # Ensure directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Model downloaded to: {output_path}")
            return output_path
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to download model: {str(e)}")


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from JSON file"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise Exception(f"Failed to load config: {str(e)}")


def create_client_from_config(config_path: str) -> HiTem3DAPIClient:
    """Create API client from configuration file"""
    config = load_config(config_path)
    hitem3d_config = config['hitem3d']
    
    return HiTem3DAPIClient(
        access_key=hitem3d_config['access_key'],
        secret_key=hitem3d_config['secret_key'],
        base_url=hitem3d_config.get('api_base_url', 'https://api.hitem3d.ai')
    )