# HiTem3D Basic Workflow

This is a clean, simple workflow that demonstrates the complete HiTem3D pipeline.

## Workflow Structure

```
[Load Image] → [Generator] → [Downloader] → [Preview]
     ↓             ↓            ↓           
[Config Node] → [Text Outputs] ←→ [Text Outputs]
```

## Nodes Included

1. **LoadImage** - Load your front image for 3D generation
2. **HiTem3DConfigNode** - Configure API credentials (runtime or persistent)
3. **HiTem3DNode (Generator)** - Submit generation request and wait for completion
4. **HiTem3DDownloaderNode** - Download the 3D model from the provided URL
5. **HiTem3DPreviewNode** - Interactive 3D preview of the downloaded model
6. **ShowText Nodes** - Display outputs for debugging:
   - Model URL from Generator
   - Cover URL from Generator  
   - Task ID from Generator

## Data Flow

1. **Image Input**: Load your front image
2. **Generation**: Generator processes image and waits for completion
3. **Outputs**: Generator returns:
   - `model_url` → Connected to Downloader
   - `cover_url` → Displayed in text node
   - `task_id` → Displayed in text node
4. **Download**: Downloader takes model_url and downloads to local file
5. **Preview**: Preview node shows interactive 3D model

## Configuration

- **Generator Settings**: Model version, resolution, format, generation type, face count, timeout
- **Downloader Settings**: File name prefix, output directory
- **Preview Settings**: Display dimensions, controls, background color

## Usage

1. Load your front image in the LoadImage node
2. Configure your API credentials in the Config node
3. Adjust generation settings in the Generator node if needed
4. Run the workflow
5. View the 3D model in the Preview node
6. Check the text outputs to see URLs and task information

This workflow demonstrates the restored original design where the Generator handles waiting and returns URLs, while the Downloader simply downloads from the provided URL.

## Requirements

- Valid HiTem3D API credentials (Access Key and Secret Key)
- Input image in supported formats (JPEG, PNG)
- Sufficient account credits for generation
- ShowText|pysssss extension for text display nodes

## Created by Geekatplay Studio

**Website:** [www.geekatplay.com](https://www.geekatplay.com)  
**Get HiTem3D Credits:** [https://www.hitem3d.ai/?sp_source=Geekatplay](https://www.hitem3d.ai/?sp_source=Geekatplay)