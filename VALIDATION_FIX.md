# VALIDATION ERROR FIX

## Issue
ComfyUI validation error due to parameter order mismatch:
- `config_data` was in the middle of widget parameters
- This caused widget_values array to be misaligned
- Face_count and generation_type values were swapped

## Root Cause
In ComfyUI:
1. Widget values correspond to INPUT_TYPES optional parameters in order
2. Connected inputs (like config_data) should not affect widget_values order
3. Function signature parameter order must match INPUT_TYPES order

## Fixes Applied

### 1. Parameter Order Fix
- Moved `config_data` to END of optional parameters in INPUT_TYPES
- Moved `config_data` to END of function signature parameters
- This ensures widget_values array maps correctly to actual widget parameters

### 2. Downloader Node Widget Values Fix
- Updated old 3-parameter format: `["", "filename", "directory"]`
- To new 2-parameter format: `["directory", timeout]`
- Fixed timeout values: 300/600 → 900 seconds (adequate for downloads)
- Aligned all workflows with new Downloader node structure

## Widget Values Order (Fixed)

### HiTem3DNode widget_values:
- [0] model: "hitem3dv1.5"
- [1] resolution: 1024  
- [2] output_format: "glb"
- [3] generation_type: "both"
- [4] face_count: 1000000
- [5] timeout: 600
- config_data comes from connection, not widget_values

### HiTem3DDownloaderNode widget_values:
- [0] output_directory: "ComfyUI/output/hitem3d/"
- [1] timeout: 900
- config_data comes from connection, not widget_values

## Status
- ✅ Fixed parameter order alignment in both nodes
- ✅ Updated all workflow Downloader timeouts to 900 seconds
- ✅ Fixed old multiview workflow structure
- ✅ Validation should now pass completely
- ⏳ Waiting for user confirmation before git commit