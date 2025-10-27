import json
import os

def add_config_node_to_workflow(workflow_path):
    """Add HiTem3D Config Node to workflow and connect it properly"""
    with open(workflow_path, 'r') as f:
        workflow = json.load(f)
    
    # Find the highest node ID and link ID
    max_node_id = max([node["id"] for node in workflow["nodes"]])
    max_link_id = workflow.get("last_link_id", 0)
    
    # Find Generator and Downloader nodes
    generator_node = None
    downloader_node = None
    
    for node in workflow["nodes"]:
        if node["type"] == "HiTem3DNode":
            generator_node = node
        elif node["type"] == "HiTem3DDownloaderNode":
            downloader_node = node
    
    if not generator_node or not downloader_node:
        print(f"Could not find required nodes in {workflow_path}")
        return
    
    # Check if config node already exists
    config_node_exists = any(node["type"] == "HiTem3DConfigNode" for node in workflow["nodes"])
    
    if config_node_exists:
        print(f"Config node already exists in {workflow_path}")
        return
    
    # Add config node
    config_node_id = max_node_id + 1
    config_node = {
        "id": config_node_id,
        "type": "HiTem3DConfigNode",
        "pos": [50, 400],
        "size": {"0": 320, "1": 150},
        "flags": {},
        "order": 0,
        "mode": 0,
        "outputs": [
            {
                "name": "config_status",
                "type": "STRING",
                "links": None,
                "shape": 3
            },
            {
                "name": "config_data",
                "type": "STRING",
                "links": [max_link_id + 1, max_link_id + 2],
                "shape": 3,
                "slot_index": 1
            }
        ],
        "properties": {"Node name for S&R": "HiTem3DConfigNode"},
        "widgets_values": [
            "YOUR_ACCESS_KEY_HERE",
            "YOUR_SECRET_KEY_HERE", 
            "https://api.hitem3d.ai",
            False
        ]
    }
    
    # Add config_data input to generator node
    if "inputs" not in generator_node:
        generator_node["inputs"] = []
    
    generator_node["inputs"].append({
        "name": "config_data",
        "type": "STRING",
        "link": max_link_id + 1
    })
    
    # Add config_data input to downloader node
    if "inputs" not in downloader_node:
        downloader_node["inputs"] = []
    
    downloader_node["inputs"].append({
        "name": "config_data", 
        "type": "STRING",
        "link": max_link_id + 2
    })
    
    # Add the config node to workflow
    workflow["nodes"].append(config_node)
    
    # Add the links
    workflow["links"].extend([
        [max_link_id + 1, config_node_id, 1, generator_node["id"], len(generator_node["inputs"]) - 1, "STRING"],
        [max_link_id + 2, config_node_id, 1, downloader_node["id"], len(downloader_node["inputs"]) - 1, "STRING"]
    ])
    
    # Update last IDs
    workflow["last_node_id"] = config_node_id
    workflow["last_link_id"] = max_link_id + 2
    
    # Save the updated workflow
    with open(workflow_path, 'w') as f:
        json.dump(workflow, f, indent=2)
    
    print(f"Updated {workflow_path} with config node")

# Update all workflow files
workflow_dir = "d:/ComfyUI/0.3.66/ComfyUI/custom_nodes/comfyui-hitem3d/examples"
workflow_files = [
    "hitem3d_basic_workflow.json",
    "hitem3d_complete_preview_workflow.json", 
    "hitem3d_multiview_preview_workflow.json"
]

for filename in workflow_files:
    filepath = os.path.join(workflow_dir, filename)
    if os.path.exists(filepath):
        add_config_node_to_workflow(filepath)
    else:
        print(f"File not found: {filepath}")

print("All workflows updated!")