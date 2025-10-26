# Example ComfyUI Workflow for HiTem3D

**Created by:** Geekatplay Studio by Vladimir Chopine  
**Website:** [www.geekatplay.com](https://www.geekatplay.com)  
**Patreon:** [https://www.patreon.com/c/geekatplay](https://www.patreon.com/c/geekatplay)  
**YouTube:** [@geekatplay](https://www.youtube.com/@geekatplay) and [@geekatplay-ru](https://www.youtube.com/@geekatplay-ru)  

## 💰 Get HiTem3D Credits
**Special Referral Link:** [https://www.hitem3d.ai/?sp_source=Geekatplay](https://www.hitem3d.ai/?sp_source=Geekatplay)

This is an example workflow that demonstrates how to use the HiTem3D nodes in ComfyUI.

## Basic Single Image Workflow

1. **Load Image** → Load your front view image
2. **HiTem3D Generator** → Generate 3D model
3. **HiTem3D Downloader** → Download the model locally

## Multi-View Workflow

1. **Load Image (Front)** → Load front view
2. **Load Image (Back)** → Load back view (optional)
3. **Load Image (Left)** → Load left view (optional)
4. **Load Image (Right)** → Load right view (optional)
5. **HiTem3D Generator** → Connect all images and generate
6. **HiTem3D Downloader** → Download the result

## Configuration Workflow

1. **HiTem3D Config** → Set your API credentials
2. **HiTem3D Generator** → Use the configured API
3. **HiTem3D Downloader** → Download results

## Tips

- Use high-quality, well-lit images for best results
- For multi-view, ensure images show the same object from different angles
- Higher resolutions take longer but produce better quality
- GLB format is recommended for most use cases
- Face count affects detail level and file size