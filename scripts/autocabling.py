import json
import logging
from pprint import pprint
from scripts.hyperfabric_api import get_fabric_nodes

# Setup logger
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_PLUGGABLE = "QDD-2Q200-CU3M"
SUPPORTED_MODELS = ["HF6100-32D", "HF6100-60L4D"]

def _get_model_name(node):
    model_name = node.get("modelName")
    if not model_name or model_name not in SUPPORTED_MODELS:
        logger.warning(f"[AUTOCABLING] Node 'f{node.get('name')}' has an unsupported modelName: f{model_name}. Autocabling has been skipped for this node.")
    return model_name

def _autocable_spine_leaf_topology(spine_nodes, leaf_nodes, pluggable):
    # First check if there are any existing connections (do this later)
    # Also check if it is being converted from mesh to spine-leaf, since you'll have to delete the leaf-leaf connections

    connections = []
    for i, spine in enumerate(spine_nodes):
        for j, leaf in enumerate(leaf_nodes):
            model_name = _get_model_name(leaf)
            if model_name is None:
                continue

            new_connection = {
                "local": { # Leaf node
                    "portName": f"Ethernet1_{i + 1 + (30 if model_name == 'HF6100-60L4D' else 0)}",
                    "nodeName": leaf.get("name") 
                },
                "remote": { # Spine node
                    "portName": f"Ethernet1_{j + 1}",
                    "nodeName": spine.get("name")
                },
                "pluggable": pluggable
            }
            connections.append(new_connection)
    
    pprint(connections)
    return connections

def _autocable_mesh_topology(nodes, pluggable):
    # First check if there are any existing connections (do this later)

    connections = []
    for i in range(0, len(nodes)):
        local_node = nodes[i]
        local_model = _get_model_name(local_node)
        if local_model is None:
            continue

        for j in range(i + 1, len(nodes)):
            remote_node = nodes[j]
            remote_model = _get_model_name(remote_node)
            if remote_model is None:
                continue

            new_connection = {
                "local": { 
                    "portName": f"Ethernet1_{j + (30 if local_model == 'HF6100-60L4D' else 0)}",
                    "nodeName": local_node.get("name") 
                },
                "remote": { 
                    "portName": f"Ethernet1_{i + 1 + (30 if remote_model == 'HF6100-60L4D' else 0)}",
                    "nodeName": remote_node.get("name")
                },
                "pluggable": pluggable
            }
            connections.append(new_connection)

    pprint(connections)
    return connections

def autocabling(autocabling_data_obj):
    get_nodes_result = get_fabric_nodes(autocabling_data_obj)
    try:
        nodes = get_nodes_result.json()
    except json.decoder.JSONDecodeError as e:
        logger.error(f"Invalid JSON in response: {e}")
        nodes = None

    if not nodes:
        logger.warning(f"[AUTOCABLING] No nodes found in fabric: {autocabling_data_obj.get('fabric_id')}")
        return []
    
    nodes = nodes["nodes"] # The result is given as {'nodes': [...]}
    spine_nodes = []
    leaf_nodes = []

    for node in nodes:
        if node.get("roles")[0] == "SPINE":
            spine_nodes.append(node)
        elif node.get("roles")[0] == "LEAF":
            leaf_nodes.append(node)
        else:
            logger.warning(f"[AUTOCABLING] Unknown node type: expected type 'LEAF' or 'SPINE', but has role: {node.get('roles')}")

    print(len(spine_nodes))
    print(len(leaf_nodes))

    # Don't overwrite port connections, but do overwrite cable

    pluggable = autocabling_data_obj["autocabling_obj"].get("pluggable")
    if not pluggable:
        pluggable = DEFAULT_PLUGGABLE

    if len(spine_nodes) > 0:
        connections = _autocable_spine_leaf_topology(spine_nodes, leaf_nodes, pluggable)
    else:
        connections = _autocable_mesh_topology(leaf_nodes, pluggable)

    # Undo overwriting here? Maybe??

    return connections