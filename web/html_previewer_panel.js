// web/html_previewer_panel.js
// HTML Previewer Frontend Extension for ComfyUI
// Created by: Geekatplay Studio by Vladimir Chopine

(function () {
  const PANEL_ID = "html-previewer-panel";
  const STORAGE_KEY = "html_previewer_last_url";
  const BUTTON_ID = "html-preview-btn";

  // Utility: create panel
  function ensurePanel() {
    let panel = document.getElementById(PANEL_ID);
    if (panel) return panel;

    panel = document.createElement("div");
    panel.id = PANEL_ID;
    panel.style.position = "fixed";
    panel.style.top = "80px";
    panel.style.right = "20px";
    panel.style.width = "600px";
    panel.style.height = "500px";
    panel.style.zIndex = 9999;
    panel.style.background = "var(--comfy-menu-bg, #202020)";
    panel.style.border = "2px solid var(--border-color, #555)";
    panel.style.borderRadius = "12px";
    panel.style.boxShadow = "0 8px 32px rgba(0,0,0,0.5)";
    panel.style.overflow = "hidden";
    panel.style.display = "none";
    panel.style.resize = "both";
    panel.style.minWidth = "400px";
    panel.style.minHeight = "300px";

    // Header with improved styling
    const header = document.createElement("div");
    header.style.padding = "12px 16px";
    header.style.display = "flex";
    header.style.gap = "12px";
    header.style.alignItems = "center";
    header.style.borderBottom = "2px solid var(--border-color, #555)";
    header.style.userSelect = "none";
    header.style.cursor = "move";
    header.style.background = "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)";
    header.style.color = "white";

    const title = document.createElement("div");
    title.textContent = "🎯 HTML Preview";
    title.style.flex = "0 0 auto";
    title.style.fontWeight = "700";
    title.style.fontSize = "16px";

    const input = document.createElement("input");
    input.type = "text";
    input.placeholder = "/html_previewer/open?path=...";
    input.style.flex = "1 1 auto";
    input.style.background = "rgba(255,255,255,0.1)";
    input.style.color = "white";
    input.style.border = "1px solid rgba(255,255,255,0.3)";
    input.style.borderRadius = "6px";
    input.style.padding = "8px 12px";
    input.style.fontSize = "14px";
    input.style.outline = "none";

    const btn = document.createElement("button");
    btn.textContent = "⚡ Load";
    btn.style.flex = "0 0 auto";
    btn.style.background = "rgba(255,255,255,0.2)";
    btn.style.color = "white";
    btn.style.border = "1px solid rgba(255,255,255,0.3)";
    btn.style.borderRadius = "6px";
    btn.style.padding = "8px 16px";
    btn.style.fontSize = "14px";
    btn.style.fontWeight = "600";
    btn.style.cursor = "pointer";
    btn.style.transition = "all 0.2s ease";

    btn.addEventListener("mouseenter", () => {
      btn.style.background = "rgba(255,255,255,0.3)";
      btn.style.transform = "translateY(-1px)";
    });

    btn.addEventListener("mouseleave", () => {
      btn.style.background = "rgba(255,255,255,0.2)";
      btn.style.transform = "translateY(0)";
    });

    const refresh = document.createElement("button");
    refresh.textContent = "🔄";
    refresh.title = "Refresh";
    refresh.style.flex = "0 0 auto";
    refresh.style.background = "rgba(255,255,255,0.2)";
    refresh.style.color = "white";
    refresh.style.border = "1px solid rgba(255,255,255,0.3)";
    refresh.style.borderRadius = "6px";
    refresh.style.padding = "8px 12px";
    refresh.style.fontSize = "14px";
    refresh.style.cursor = "pointer";
    refresh.style.transition = "all 0.2s ease";

    const close = document.createElement("button");
    close.textContent = "×";
    close.title = "Close";
    close.style.flex = "0 0 auto";
    close.style.background = "rgba(255,255,255,0.2)";
    close.style.color = "white";
    close.style.border = "1px solid rgba(255,255,255,0.3)";
    close.style.borderRadius = "6px";
    close.style.padding = "8px 12px";
    close.style.fontSize = "16px";
    close.style.fontWeight = "bold";
    close.style.cursor = "pointer";
    close.style.transition = "all 0.2s ease";

    header.append(title, input, btn, refresh, close);

    // Status bar
    const statusBar = document.createElement("div");
    statusBar.style.padding = "8px 16px";
    statusBar.style.background = "var(--comfy-input-bg, #2a2a2a)";
    statusBar.style.borderBottom = "1px solid var(--border-color, #555)";
    statusBar.style.fontSize = "12px";
    statusBar.style.color = "var(--descrip-text, #aaa)";
    statusBar.textContent = "Ready - Waiting for content...";

    // iframe container
    const iframeContainer = document.createElement("div");
    iframeContainer.style.position = "relative";
    iframeContainer.style.height = "calc(100% - 100px)";
    iframeContainer.style.background = "var(--comfy-input-bg, #2a2a2a)";

    const iframe = document.createElement("iframe");
    iframe.style.width = "100%";
    iframe.style.height = "100%";
    iframe.style.border = "0";
    iframe.style.borderRadius = "0 0 10px 10px";
    iframe.referrerPolicy = "no-referrer";

    // Loading overlay
    const loadingOverlay = document.createElement("div");
    loadingOverlay.style.position = "absolute";
    loadingOverlay.style.top = "0";
    loadingOverlay.style.left = "0";
    loadingOverlay.style.right = "0";
    loadingOverlay.style.bottom = "0";
    loadingOverlay.style.background = "rgba(0,0,0,0.8)";
    loadingOverlay.style.display = "flex";
    loadingOverlay.style.alignItems = "center";
    loadingOverlay.style.justifyContent = "center";
    loadingOverlay.style.color = "white";
    loadingOverlay.style.fontSize = "16px";
    loadingOverlay.style.zIndex = "10";
    loadingOverlay.innerHTML = '<div style="text-align: center;"><div style="font-size: 24px; margin-bottom: 8px;">🔄</div><div>Loading HTML Preview...</div></div>';
    loadingOverlay.style.display = "none";

    iframeContainer.append(iframe, loadingOverlay);
    panel.append(header, statusBar, iframeContainer);
    document.body.appendChild(panel);

    // Drag support for header
    (function makeDraggable(target, handle) {
      let sx=0, sy=0, ox=0, oy=0, dragging=false;
      handle.addEventListener("pointerdown", (e)=>{
        dragging = true;
        sx = e.clientX; sy = e.clientY;
        const rect = target.getBoundingClientRect();
        ox = rect.left; oy = rect.top;
        handle.setPointerCapture(e.pointerId);
        e.preventDefault();
      });
      handle.addEventListener("pointermove", (e)=>{
        if (!dragging) return;
        const dx = e.clientX - sx;
        const dy = e.clientY - sy;
        target.style.left = (ox + dx) + "px";
        target.style.top  = (oy + dy) + "px";
        target.style.right = "auto";
        e.preventDefault();
      });
      handle.addEventListener("pointerup", ()=> dragging = false);
    })(panel, header);

    // Actions
    function updateStatus(message, type = "info") {
      statusBar.textContent = message;
      statusBar.style.color = type === "error" ? "#ff6b6b" : 
                             type === "success" ? "#51cf66" : 
                             "var(--descrip-text, #aaa)";
    }

    function loadURL(u) {
      if (!u) {
        updateStatus("No URL provided", "error");
        return;
      }
      if (!u.startsWith("/")) {
        updateStatus("Only server-relative URLs are allowed (must start with /)", "error");
        alert("Only server-relative URLs are allowed (must start with /)");
        return;
      }
      
      loadingOverlay.style.display = "flex";
      updateStatus("Loading...", "info");
      
      iframe.src = u;
      localStorage.setItem(STORAGE_KEY, u);
      panel.style.display = "block";
      
      // Hide loading overlay after a short delay
      setTimeout(() => {
        loadingOverlay.style.display = "none";
        updateStatus(`Loaded: ${u}`, "success");
      }, 1000);
    }

    function refreshIframe() {
      const currentUrl = input.value.trim();
      if (currentUrl) {
        // Add a timestamp to force refresh
        const separator = currentUrl.includes("?") ? "&" : "?";
        const refreshUrl = `${currentUrl}${separator}_refresh=${Date.now()}`;
        iframe.src = refreshUrl;
        updateStatus("Refreshed preview", "success");
      }
    }

    btn.addEventListener("click", ()=> loadURL(input.value.trim()));
    input.addEventListener("keydown", (e)=> { 
      if (e.key === "Enter") loadURL(input.value.trim()); 
    });
    refresh.addEventListener("click", refreshIframe);
    close.addEventListener("click", ()=> { 
      panel.style.display = "none"; 
      updateStatus("Preview closed", "info");
    });

    // Restore last URL
    const last = localStorage.getItem(STORAGE_KEY);
    if (last) {
      input.value = last;
      updateStatus("Last URL restored", "info");
    }

    // Expose API for other scripts (selection sync)
    window.__HTML_PREVIEWER__ = {
      show: () => { 
        panel.style.display = "block"; 
        updateStatus("Preview panel opened", "info");
      },
      load: (u) => { 
        input.value = u; 
        loadURL(u); 
      },
      set: (u) => { 
        input.value = u; 
        localStorage.setItem(STORAGE_KEY, u); 
        updateStatus("URL updated", "info");
      },
      refresh: refreshIframe,
      panel: panel
    };

    return panel;
  }

  // Add toolbar button
  function addToolbarButton() {
    // Prevent duplicate buttons
    if (document.getElementById(BUTTON_ID)) return;

    const panel = ensurePanel();

    // Try to find ComfyUI header areas
    const headerSelectors = [
      ".comfyui-menu",
      "#comfyui-header", 
      ".comfy-header",
      ".top-bar",
      ".menu-bar",
      "body"
    ];

    let header = null;
    for (const selector of headerSelectors) {
      header = document.querySelector(selector);
      if (header) break;
    }

    const btn = document.createElement("button");
    btn.id = BUTTON_ID;
    btn.innerHTML = "🎯 HTML Preview";
    btn.style.marginLeft = "8px";
    btn.style.marginRight = "8px";
    btn.style.padding = "8px 12px";
    btn.style.background = "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)";
    btn.style.color = "white";
    btn.style.border = "none";
    btn.style.borderRadius = "6px";
    btn.style.fontSize = "14px";
    btn.style.fontWeight = "600";
    btn.style.cursor = "pointer";
    btn.style.transition = "all 0.2s ease";
    btn.style.boxShadow = "0 2px 8px rgba(245, 158, 11, 0.3)";

    btn.addEventListener("mouseenter", () => {
      btn.style.transform = "translateY(-1px)";
      btn.style.boxShadow = "0 4px 12px rgba(245, 158, 11, 0.4)";
    });

    btn.addEventListener("mouseleave", () => {
      btn.style.transform = "translateY(0)";
      btn.style.boxShadow = "0 2px 8px rgba(245, 158, 11, 0.3)";
    });

    btn.addEventListener("click", () => {
      const isVisible = panel.style.display === "block";
      panel.style.display = isVisible ? "none" : "block";
      
      if (!isVisible) {
        // Try to auto-detect HTML previewer URLs from selected nodes
        detectAndLoadFromSelection();
      }
    });

    // Place button
    (header || document.body).appendChild(btn);
    
    console.log("[HTMLPreviewer] Toolbar button added to", header?.tagName || "body");
  }

  // Auto-detect HTML previewer URLs from node selection
  function detectAndLoadFromSelection() {
    try {
      const app = window.app;
      if (!app || !app.graph) return;

      const selectedNodes = app.canvas.selected_nodes || {};
      
      for (const nodeId in selectedNodes) {
        const node = selectedNodes[nodeId];
        if (!node) continue;

        // Check if this is an HTMLPreviewer node
        if (node.comfyClass === "HTMLPreviewer" || node.type === "HTMLPreviewer") {
          // Look for the output widget or last execution result
          const outputs = node.outputs || [];
          for (const output of outputs) {
            if (output.value && typeof output.value === "string" && 
                output.value.startsWith("/html_previewer/open")) {
              
              if (window.__HTML_PREVIEWER__) {
                window.__HTML_PREVIEWER__.load(output.value);
                return;
              }
            }
          }
        }

        // Check widgets for HTML previewer URLs
        const widgets = node.widgets || [];
        for (const widget of widgets) {
          if (widget.value && typeof widget.value === "string" && 
              widget.value.startsWith("/html_previewer/open")) {
            
            if (window.__HTML_PREVIEWER__) {
              window.__HTML_PREVIEWER__.load(widget.value);
              return;
            }
          }
        }
      }
    } catch (e) {
      console.warn("[HTMLPreviewer] Selection detection error:", e);
    }
  }

  // Listen for node selection changes
  function installSelectionWatcher() {
    try {
      const app = window.app;
      if (!app || !app.graph) {
        // Retry later if app not ready
        setTimeout(installSelectionWatcher, 1000);
        return;
      }

      // Hook into selection changes
      const originalSelectNode = app.canvas.selectNode;
      if (originalSelectNode) {
        app.canvas.selectNode = function(node, add) {
          const result = originalSelectNode.call(this, node, add);
          
          // Check if selected node has HTML preview URLs
          setTimeout(() => {
            detectAndLoadFromSelection();
          }, 100);
          
          return result;
        };
      }

      console.log("[HTMLPreviewer] Selection watcher installed");
    } catch (e) {
      console.warn("[HTMLPreviewer] Selection watcher install failed:", e);
    }
  }

  // Initialize after DOM is ready
  function initialize() {
    try {
      ensurePanel();
      addToolbarButton();
      installSelectionWatcher();
      console.log("[HTMLPreviewer] Frontend extension loaded successfully");
    } catch (e) {
      console.error("[HTMLPreviewer] Initialization error:", e);
    }
  }

  // Multiple initialization triggers to ensure loading
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialize);
  } else {
    initialize();
  }

  // Fallback initialization after a delay
  setTimeout(initialize, 2000);

  // Export for debugging
  window.HTMLPreviewerExtension = {
    initialize,
    ensurePanel,
    addToolbarButton,
    detectAndLoadFromSelection
  };

})();