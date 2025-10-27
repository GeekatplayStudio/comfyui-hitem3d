# 🎯 ComfyUI HiTem3D Examples

This folder contains comprehensive examples, workflows, and test files for the ComfyUI HiTem3D package, including the new HTML Previewer functionality.

## 📁 **File Organization**

### **🎯 HTML Previewer Workflows**

#### **Basic Examples**
- **`html_previewer_simple_demo.json`** - Quick start guide with basic HTML previewer usage
- **`html_previewer_demo.json`** - Standalone demo with interactive HTML content

#### **Advanced Examples**  
- **`html_previewer_advanced_demo.json`** - Dynamic dashboards, charts, and interactive games
- **`html_previewer_complete_workflow.json`** - Full HiTem3D + HTML preview integration
- **`html_previewer_workflow.json`** - Basic HiTem3D integration example

### **🎨 HiTem3D Workflows**

#### **Core Workflows**
- **`hitem3d_basic_workflow.json`** - Standard 3D model generation workflow
- **`hitem3d_modern_preview_workflow.json`** - Enhanced 3D preview with modern UI
- **`hitem3d_preview_test_workflow.json`** - Simple preview testing workflow

### **🧪 Test & Demo Files**

#### **Python Test Scripts**
- **`test_enhanced_preview.py`** - Enhanced preview system testing
- **`test_large_file_demo.py`** - Large file handling demonstration
- **`test_large_file_handling.py`** - File size optimization tests
- **`test_preview.py`** - General preview functionality tests
- **`test_preview_node.py`** - Preview node unit tests
- **`test_preview_with_file.py`** - File-based preview testing

#### **HTML Demo Files**
- **`enhanced_preview_demo.html`** - Modern HiTem3D-style HTML preview example

#### **Documentation**
- **`README.md`** - Basic package documentation
- **`IMAGE_SETUP.md`** - Image setup instructions

## 🚀 **Quick Start Guide**

### **1. HTML Previewer - Basic Usage**
```bash
# Load the simple demo workflow
Import: html_previewer_simple_demo.json
```
**Features:**
- Raw HTML content preview
- File path methods (base_dir + file_name, absolute_path)
- Auto-refresh token demonstration

### **2. HTML Previewer - Advanced Features**
```bash
# Load the advanced demo workflow
Import: html_previewer_advanced_demo.json
```
**Features:**
- Dynamic dashboard generation
- Interactive charts and graphs
- Mini-game with JavaScript functionality
- Real-time statistics and progress bars

### **3. Complete HiTem3D Integration**
```bash
# Load the complete workflow
Import: html_previewer_complete_workflow.json
```
**Features:**
- Full pipeline: Image → 3D Model → HTML Preview
- Auto-refresh with dynamic tokens
- Modern UI integration
- Professional preview system

## 📋 **Workflow Usage Instructions**

### **Step 1: Import Workflow**
1. Open ComfyUI
2. Click "Load" button
3. Select any `.json` file from this folder
4. Workflow loads automatically

### **Step 2: Configure Nodes**
1. **For HiTem3D workflows**: Add your API credentials in Config nodes
2. **For HTML Previewer**: Modify HTML content in Text nodes
3. **For file-based previews**: Update file paths to match your system

### **Step 3: Run Workflow**
1. Click "Queue Prompt" to execute
2. Watch nodes execute in sequence
3. Preview URLs generate automatically

### **Step 4: View HTML Preview**
1. Click **🎯 HTML Preview** button in toolbar
2. Preview panel opens with your content
3. Interact with buttons, animations, and features

## 🛠️ **Customization Tips**

### **HTML Content Customization**
```html
<!-- Modify HTML in Text nodes -->
<style>
    body { background: linear-gradient(45deg, #your-color1, #your-color2); }
</style>
```

### **Auto-Refresh Setup**
```json
// Connect changing values to auto_refresh_token
"auto_refresh_token": "{{time()}}"  // or any dynamic value
```

### **File Path Configuration**
```json
// Method 1: Base directory + filename
"base_dir": "D:\\Your\\HTML\\Directory",
"file_name": "your_file.html"

// Method 2: Absolute path
"absolute_path": "D:\\Full\\Path\\To\\Your\\File.html"
```

## 🎯 **HTML Previewer Node Reference**

### **Input Parameters**
| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `html_content` | STRING | Raw HTML content | `<h1>Hello World!</h1>` |
| `base_dir` | STRING | Base directory path | `D:\ComfyUI\output` |
| `file_name` | STRING | HTML filename | `preview.html` |
| `absolute_path` | STRING | Complete file path | `D:\path\to\file.html` |
| `auto_refresh_token` | STRING | Refresh trigger | `{{time()}}` or any changing value |

### **Output**
- **`preview_url`**: Server URL for HTML preview access

## 📊 **Example Scenarios**

### **Scenario 1: Dynamic Content Generation**
```
Text Node (HTML Template) → HTMLPreviewer → ShowText (URL)
```
Perfect for: Data visualization, reports, dynamic dashboards

### **Scenario 2: File-Based Previews**
```
HTMLPreviewer (with file path) → ShowText (URL)
```
Perfect for: Existing HTML files, static content, documentation

### **Scenario 3: HiTem3D Integration**
```
HiTem3D Pipeline → HiTem3DPreviewNode → HTMLPreviewer → ShowText
```
Perfect for: 3D model previews, enhanced UI, professional workflows

### **Scenario 4: Auto-Refreshing Dashboards**
```
Dynamic Token → HTMLPreviewer (with HTML content) → Live Preview
```
Perfect for: Real-time monitoring, live data, interactive applications

## 🔧 **Testing & Development**

### **Run Python Tests**
```bash
# Test basic preview functionality
python test_preview.py

# Test enhanced preview system
python test_enhanced_preview.py

# Test large file handling
python test_large_file_handling.py
```

### **HTML File Testing**
```bash
# Open demo HTML file in browser
enhanced_preview_demo.html
```

## 🛡️ **Security Notes**

### **Allowed File Paths**
- ComfyUI output directory (automatic)
- Node temp directory (automatic)
- Custom paths via environment variable: `HTML_PREVIEW_ALLOWED_ROOTS`

### **File Type Restrictions**
- Only `.html` and `.htm` files allowed
- No remote URLs (`http://`, `https://`)
- Path validation prevents directory traversal

## 📱 **Browser Compatibility**

### **Tested Browsers**
- ✅ Chrome/Chromium (recommended)
- ✅ Firefox
- ✅ Edge
- ✅ Safari

### **Required Features**
- Modern CSS support (flexbox, grid)
- JavaScript ES6+
- Local file serving support

## 🎨 **Styling Examples**

### **Modern Gradient Backgrounds**
```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

### **Glass Morphism Effects**
```css
background: rgba(255,255,255,0.1);
backdrop-filter: blur(20px);
border-radius: 20px;
```

### **Interactive Animations**
```css
transition: all 0.3s ease;
transform: translateY(-5px);
```

## 📚 **Additional Resources**

- **Main Documentation**: `../HTML_PREVIEWER_README.md`
- **HiTem3D API**: [hitem3d.ai](https://hitem3d.ai)
- **Geekatplay Studio**: [geekatplay.com](https://geekatplay.com)
- **YouTube Tutorials**: [@geekatplay](https://youtube.com/@geekatplay)

## 🤝 **Contributing**

1. Create new example workflows
2. Add HTML templates and demos
3. Write test scripts for edge cases
4. Document usage patterns
5. Submit pull requests

## 📄 **License**

All examples are part of the HiTem3D ComfyUI package.

---

**🎯 Ready to explore? Start with `html_previewer_simple_demo.json` for a quick introduction!**

*Created with ❤️ by **Geekatplay Studio***