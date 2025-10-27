# 🔑 HiTem3D Configuration Guide

## ✅ **NEW: Runtime Configuration Support**

The HiTem3D nodes now support **two ways** to provide API credentials:

### **1. Runtime Configuration (Recommended for Security)**
- Use the **HiTem3D Config Node** in your workflow
- Enter your API keys directly in the node
- Set `save_config` to `False` to keep credentials in memory only
- ✅ **Secure**: No credentials saved to disk
- ✅ **Flexible**: Different keys per workflow

### **2. File Configuration (Permanent Storage)**
- Use the **HiTem3D Config Node** with `save_config` set to `True`
- Or manually edit `config.json` file
- ✅ **Convenient**: Set once, use everywhere
- ⚠️ **Note**: Credentials saved to disk

---

## 🎯 **How It Works:**

### **Priority Order:**
1. **Runtime Config** (from Config Node) - *Highest Priority*
2. **File Config** (from config.json) - *Fallback*

### **Node Connection Flow:**
```
[HiTem3D Config Node] → [Generator Node] → [Downloader Node]
         ↓                      ↓                ↓
    config_data           config_data      config_data
```

---

## 🔧 **Setup Instructions:**

### **Option A: Runtime Configuration (Secure)**

1. **Add Config Node** to your workflow
2. **Connect** the `config_data` output to:
   - Generator Node's `config_data` input
   - Downloader Node's `config_data` input
3. **Enter your API keys** in the Config Node:
   - Access Key: `your_actual_access_key`
   - Secret Key: `your_actual_secret_key`
4. **Set save_config to `False`** (default)
5. **Run the workflow** - credentials stay in memory only

### **Option B: File Configuration (Permanent)**

1. **Add Config Node** to your workflow
2. **Connect** as above
3. **Enter your API keys** in the Config Node
4. **Set save_config to `True`**
5. **Run once** - credentials saved to `config.json`
6. **Future workflows** will use saved credentials automatically

---

## 📋 **All Workflows Now Include Config Node**

Every example workflow now includes the HiTem3D Config Node:

- ✅ `hitem3d_basic_workflow.json`
- ✅ `hitem3d_showcase_preview_workflow.json`
- ✅ `hitem3d_complete_preview_workflow.json`
- ✅ `hitem3d_multiview_preview_workflow.json`
- ✅ `hitem3d_test_preview_simple.json`

---

## 🔒 **Security Best Practices:**

### **For Personal Use:**
- Use **File Configuration** for convenience
- Keep `config.json` in `.gitignore` (already included)

### **For Sharing/Publishing:**
- Use **Runtime Configuration** only
- Never save credentials to file when sharing workflows
- Set `save_config = False` in shared workflows

### **For Development:**
- Always use placeholder values in repository
- Use `.env` files for development credentials (not implemented yet)

---

## 🛠️ **Configuration Node Settings:**

| Setting | Description | Recommended |
|---------|-------------|-------------|
| `access_key` | Your HiTem3D Access Key | Required |
| `secret_key` | Your HiTem3D Secret Key | Required |
| `api_base_url` | API endpoint | `https://api.hitem3d.ai` |
| `save_config` | Save to config.json | `False` for security |

---

## 🎯 **Example Connection Pattern:**

```
LoadImage ──IMAGE──> HiTem3DNode ──task_id──> HiTem3DDownloaderNode ──model_path──> HiTem3DPreviewNode
                          ↑                            ↑
                    config_data                  config_data
                          ↑                            ↑
                     HiTem3DConfigNode ──config_data──┴─────────────────┘
```

---

## ❌ **Common Issues & Solutions:**

### **Issue**: "Config file not found"
**Solution**: Use Config Node with runtime configuration

### **Issue**: "Invalid credentials"  
**Solution**: Check your API keys in the Config Node

### **Issue**: "Nodes not connecting"
**Solution**: Ensure `config_data` output connects to both Generator and Downloader

### **Issue**: "Workflow missing config"
**Solution**: Use updated workflow examples that include Config Node

---

## 🆕 **Migration from Old Workflows:**

If you have old workflows without Config Node:

1. **Add HiTem3D Config Node** to workflow
2. **Connect** `config_data` output to Generator and Downloader inputs
3. **Enter your API credentials**
4. **Set save_config** according to your security preference

---

## 🎉 **Benefits:**

- ✅ **No more missing config errors**
- ✅ **Flexible credential management** 
- ✅ **Better security** with runtime-only config
- ✅ **Backward compatibility** with file config
- ✅ **All workflows ready-to-use** with config included

---

**Get HiTem3D API Keys:** [hitem3d.ai/?sp_source=Geekatplay](https://hitem3d.ai/?sp_source=Geekatplay)

Created by: **Geekatplay Studio by Vladimir Chopine**  
Website: **[www.geekatplay.com](https://www.geekatplay.com)**