# HTML Previewer System for ComfyUI

## 🎯 Overview

The HTML Previewer System is a comprehensive solution for displaying HTML content directly within ComfyUI. It features a complete ecosystem of nodes for dynamic content generation, template processing, and live preview capabilities with auto-refresh functionality.

## ✨ Complete Feature Set

### 🚀 **Core HTML Preview**
- **Live HTML Preview**: Floating, draggable preview panel within ComfyUI
- **Auto-Refresh Detection**: Automatic updates when content changes
- **Secure File Serving**: Path validation with whitelist protection
- **Interactive Controls**: Drag, resize, and manage preview windows

### 🔄 **Dynamic Content System**
- **Dynamic Value Generator**: Create timestamps, counters, UUIDs, random values
- **Text Template Engine**: Process templates with `{{placeholder}}` syntax
- **Auto-Refresh Tokens**: Trigger preview updates automatically
- **Built-in Variables**: Access to date, time, and custom values

### 🛡️ **Security Features**
- **Path Whitelist**: Only allowed directories can be accessed
- **File Type Validation**: Restricted to `.html` and `.htm` files
- **CSP Headers**: Content Security Policy protection
- **No Remote URLs**: Blocks external HTTP/HTTPS requests

## 📦 Node Collection

### 1. HTML Previewer (Local)
**Main preview node for displaying HTML content**

**Inputs:**
- `html_content` (STRING): Raw HTML content to display
- `auto_refresh_token` (STRING): Token that triggers refresh when changed

**Outputs:**
- `preview_url` (STRING): URL for accessing the preview

**Features:**
- 🎯 Floating preview panel with drag support
- 🔄 Auto-refresh when token changes
- 🛡️ Secure file serving with validation

### 2. Dynamic Value Generator
**Generates dynamic values for auto-refresh and templating**

**Inputs:**
- `value_type` (ENUM): Type of value to generate
  - `timestamp`: Current date/time
  - `counter`: Incremental counter
  - `uuid`: Unique identifier
  - `random`: Random number
  - `custom`: Custom unix timestamp
- `custom_prefix` (STRING): Optional prefix for values
- `counter_start` (INT): Starting value for counter mode
- `format_string` (STRING): Format for timestamp values

**Outputs:**
- `dynamic_value` (STRING): Generated dynamic value

**Value Types:**
- **Timestamp**: `2025-10-26_14:30:22` (configurable format)
- **Counter**: `1, 2, 3...` (incremental)
- **UUID**: `a1b2c3d4` (8-character short UUID)
- **Random**: `7432` (4-digit random number)
- **Custom**: `refresh_1729950622` (unix timestamp with prefix)

### 3. Text Template
**Processes templates with dynamic placeholders**

**Inputs:**
- `template` (STRING): Text template with `{{placeholder}}` syntax
- `value1`, `value2`, `value3` (STRING): Dynamic values for template
- `timestamp_format` (STRING): Format for built-in timestamps

**Outputs:**
- `text_output` (STRING): Processed template with values

**Built-in Placeholders:**
```html
{{timestamp}} - Current timestamp
{{date}} - Current date (YYYY-MM-DD)
{{unix}} - Unix timestamp
{{year}}, {{month}}, {{day}} - Date components
{{hour}}, {{minute}}, {{second}} - Time components
{{value1}}, {{value2}}, {{value3}} - Input values
```

**Example Template:**
```html
<!DOCTYPE html>
<html>
<head><title>Dynamic Content</title></head>
<body>
    <h1>Auto-Refresh Demo</h1>
    <p>Generated at: {{timestamp}}</p>
    <p>Refresh token: {{value1}}</p>
    <p>Unix time: {{unix}}</p>
</body>
</html>
```
set HTML_PREVIEW_ALLOWED_ROOTS=D:\Projects\HTML;C:\MyFiles\Web
```

### 3. **Frontend Loading**
The JavaScript extension loads automatically when ComfyUI starts. Look for the **🎯 HTML Preview** button in the toolbar.

## 🚀 Usage Guide

### **Method 1: Raw HTML Content**
1. Add an **HTML Previewer** node to your workflow
2. Enter HTML content in the `html_content` field
3. Queue the workflow
4. Click **🎯 HTML Preview** button in toolbar
5. The preview loads automatically

### **Method 2: File Path**
1. Add an **HTML Previewer** node
2. Set `absolute_path` to an HTML file (or use `base_dir` + `file_name`)
3. Queue the workflow
4. Preview URL appears in node output
5. Use the toolbar button to view

### **Method 3: Auto-Refresh**
1. Connect a **Text** node to `auto_refresh_token`
2. Use changing values like timestamps or counters
3. Each queue will refresh the preview automatically

## 📊 Node Parameters

### **Inputs**
| Parameter | Type | Description |
|-----------|------|-------------|
| `base_dir` | STRING | Base directory path (optional) |
| `file_name` | STRING | HTML filename (optional) |
| `absolute_path` | STRING | Full path to HTML file (takes precedence) |
| `auto_refresh_token` | STRING | Change this value to force refresh |
| `html_content` | STRING | Raw HTML content (multiline) |

### **Outputs**
| Output | Type | Description |
|--------|------|-------------|
| `preview_url` | STRING | Server URL for preview access |

## 🎮 Frontend Controls

### **Toolbar Button**
- **🎯 HTML Preview**: Toggle preview panel visibility
- **Smart Detection**: Automatically detects HTML previewer nodes

### **Preview Panel**
- **URL Input**: Manually enter preview URLs
- **⚡ Load**: Load the entered URL
- **🔄 Refresh**: Force refresh current preview
- **×**: Close preview panel
- **Drag Header**: Move panel around screen
- **Resize**: Drag corners to resize

## 🔐 Security Implementation

### **Path Validation**
```python
def _is_allowed(path: str) -> bool:
    """Check if a file path is allowed for serving"""
    # File must exist and have .html/.htm extension
    # Path must be within allowed root directories
    # No directory traversal attacks (..)
```

### **HTTP Route Protection**
```python
@PromptServer.instance.routes.get("/html_previewer/open")
def html_previewer_open(path: str = "", base: str = "", file: str = ""):
    # URL decoding and validation
    # Remote URL blocking
    # Path whitelist checking
    # CSP header injection
```

## 📋 Example Workflows

### **Basic HTML Preview**
```json
{
  "HTMLPreviewer": {
    "html_content": "<h1>Hello World!</h1><p>This is a test.</p>"
  }
}
```

### **File Preview with Auto-Refresh**
```json
{
  "HTMLPreviewer": {
    "absolute_path": "C:/MyProject/index.html",
    "auto_refresh_token": "{{time()}}"
  }
}
```

### **HiTem3D Integration**
```json
{
  "HiTem3DPreviewNode": {
    "output": ["preview_html", "preview_file_path", "preview_url"]
  },
  "HTMLPreviewer": {
    "html_content": "{{HiTem3DPreviewNode.preview_html}}",
    "auto_refresh_token": "{{timestamp}}"
  }
}
```

## 🚨 Troubleshooting

### **Common Issues**

**1. "Path not allowed" error**
- Ensure file is in ComfyUI output directory
- Check environment variable `HTML_PREVIEW_ALLOWED_ROOTS`
- Verify file has `.html` or `.htm` extension

**2. "HTML Previewer not available" message**
- ComfyUI server imports missing
- Check ComfyUI version compatibility (requires 0.3.6x+)

**3. Preview panel not appearing**
- Check browser console for JavaScript errors
- Ensure ComfyUI frontend loaded completely
- Try refreshing ComfyUI page

**4. Auto-refresh not working**
- Verify `auto_refresh_token` is actually changing
- Check node connection in workflow
- Ensure queue execution is completing

### **Debug Commands**
```javascript
// Check if extension loaded
console.log(window.HTMLPreviewerExtension);

// Manual panel trigger
window.__HTML_PREVIEWER__.show();

// Check available API
console.log(window.__HTML_PREVIEWER__);
```

## 🎯 Integration Examples

### **With HiTem3D Preview**
The HTML Previewer seamlessly integrates with HiTem3D's existing preview system:

```python
# HiTem3D generates enhanced HTML
preview_html = hitem3d_preview_node.generate_preview()

# HTML Previewer displays it
html_previewer = HTMLPreviewer()
preview_url = html_previewer.make_url(html_content=preview_html)
```

### **With Dynamic Content**
```python
# Generate dynamic HTML based on model data
html_content = f"""
<h1>Model: {model_name}</h1>
<p>Size: {file_size} MB</p>
<p>Generated: {timestamp}</p>
"""

# Preview updates automatically
preview_url = html_previewer.make_url(
    html_content=html_content,
    auto_refresh_token=str(time.time())
)
```

## 🔄 API Reference

### **Backend API**
```python
class HTMLPreviewer:
    def make_url(self, base_dir="", file_name="", absolute_path="", 
                 auto_refresh_token="", html_content="") -> Tuple[str]:
        # Returns (preview_url,)
```

### **Frontend API**
```javascript
window.__HTML_PREVIEWER__ = {
    show(),           // Show preview panel
    load(url),        // Load URL and show panel
    set(url),         // Set URL without loading
    refresh(),        // Refresh current preview
    panel            // Direct panel element access
}
```

### **HTTP Endpoints**
```
GET /html_previewer/open?path=<file_path>
GET /html_previewer/open?base=<base_dir>&file=<filename>
```

## 🎨 Customization

### **Panel Styling**
Modify `web/html_previewer_panel.js` to customize:
- Colors and themes
- Panel size and position
- Button layouts
- Animation effects

### **Security Settings**
Edit `nodes.py` to adjust:
- Allowed file extensions
- CSP headers
- Path validation rules
- Error messages

## 📈 Performance Notes

- **Memory Efficient**: HTML content is served on-demand
- **Fast Loading**: Minimal JavaScript overhead
- **Scalable**: Handles large HTML files efficiently
- **Browser Cache**: Leverages browser caching for performance

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Test with multiple HTML scenarios
4. Ensure security measures remain intact
5. Submit pull request

## 📄 License

This HTML Previewer extension is part of the HiTem3D ComfyUI package.

Created with ❤️ by **Geekatplay Studio**
- Website: [www.geekatplay.com](https://www.geekatplay.com)
- YouTube: [@geekatplay](https://youtube.com/@geekatplay)
- Patreon: [geekatplay](https://patreon.com/geekatplay)

---

**🎯 Ready to preview HTML in ComfyUI? Load the demo workflow and start creating!**