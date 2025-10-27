# 🎯 HiTem3D Node Connection Guide

## ✅ **FIXED: Preview Node Connection & Timestamped Downloads**

### **How to Connect HiTem3D Nodes:**

```
[Load Image] → [HiTem3D Generator] → [HiTem3D Downloader] → [HiTem3D Preview]
     ↓               ↓                     ↓                    ↓
   IMAGE          task_id              model_path           preview_html
```

### **Step-by-Step Connection:**

1. **Load Image Node** 
   - Connect `IMAGE` output to HiTem3D Generator's `front_image` input

2. **HiTem3D Generator Node**
   - Connect `task_id` output to HiTem3D Downloader's `task_id` input
   - ⚠️ **Important**: Generator only returns `task_id` now (not model_url)

3. **HiTem3D Downloader Node**
   - Connect `model_path` output to HiTem3D Preview's `model_path` input
   - ✅ **NEW**: Automatically downloads with timestamp to avoid overwriting
   - ✅ **NEW**: Waits for task completion automatically

4. **HiTem3D Preview Node**
   - Shows interactive 3D preview of the downloaded model
   - Supports: GLB, OBJ, STL, FBX formats

---

## 🔧 **Recent Fixes:**

### **✅ Automatic Timestamped File Names**
- **Before**: Files were overwritten (`model.glb`)
- **After**: Unique timestamps (`hitem3d_model_20241026_143052.glb`)

### **✅ Correct Node Connections**
- **Before**: Preview tried to connect directly to Generator
- **After**: Preview connects to Downloader's `model_path` output

### **✅ Simplified Workflow**
- **Before**: Complex multi-output nodes
- **After**: Clean single-purpose nodes with clear data flow

---

## 📁 **File Naming Convention:**

Downloaded models are automatically named with timestamps:
```
hitem3d_model_YYYYMMDD_HHMMSS.extension

Examples:
- hitem3d_model_20241026_143052.glb
- hitem3d_model_20241026_143155.obj
- hitem3d_model_20241026_143301.stl
```

---

## 🎮 **3D Preview Features:**

- **Interactive Controls**: Mouse to rotate, zoom, pan
- **Multiple Formats**: GLB, GLTF, OBJ, STL, FBX support
- **Visual Options**: Wireframe, grid, auto-rotate
- **Background Colors**: Black, white, gray options
- **Responsive Size**: Adjustable width/height

---

## 🚀 **Example Workflows:**

1. **`hitem3d_test_preview_simple.json`** - Basic test workflow
2. **`hitem3d_showcase_preview_workflow.json`** - Complete showcase
3. **`hitem3d_multiview_preview_workflow.json`** - Multi-view generation
4. **`hitem3d_complete_preview_workflow.json`** - Advanced options

---

## ⚠️ **Common Issues Fixed:**

### **Issue**: "Preview node not working"
**Solution**: Connect Preview to Downloader's `model_path`, not Generator

### **Issue**: "Files getting overwritten"
**Solution**: Now uses automatic timestamps in filenames

### **Issue**: "Model not found"
**Solution**: Downloader now waits for task completion automatically

---

## 📝 **Migration from Old Workflows:**

If you have old workflows, update the connections:

**Old Connection:**
```
Generator.model_url → Preview.model_path  ❌
```

**New Connection:**
```
Generator.task_id → Downloader.task_id → Downloader.model_path → Preview.model_path  ✅
```

---

Created by: **Geekatplay Studio by Vladimir Chopine**  
Website: **[www.geekatplay.com](https://www.geekatplay.com)**  
Get HiTem3D Credits: **[hitem3d.ai/?sp_source=Geekatplay](https://hitem3d.ai/?sp_source=Geekatplay)**