import json
from pprint import pprint
from collections import defaultdict
from program_files.utils.logger import get_logger
from program_files.scripts.hyperfabric_api import get_fabric, get_fabric_nodes, get_fabric_connections

# Setup logger
logger = get_logger()

cables = [
    # 400G cables
    {"name": "QDD-400-CU1M", "speed": 400, "length": 1},
    {"name": "QDD-400-CU2M", "speed": 400, "length": 2},
    {"name": "QDD-400-CU2.5M", "speed": 400, "length": 2.5},
    {"name": "QDD-400-CU3M", "speed": 400, "length": 3},
    {"name": "QDD-400-AOC5M", "speed": 400, "length": 5},
    {"name": "QDD-400-AOC7M", "speed": 400, "length": 7},
    {"name": "QDD-400-AOC10M", "speed": 400, "length": 10},
    {"name": "QDD-400-AOC15M", "speed": 400, "length": 15},
    {"name": "QDD-400-AOC20M", "speed": 400, "length": 20},
    {"name": "QDD-400-AOC25M", "speed": 400, "length": 25},
    {"name": "QDD-400-AOC30M", "speed": 400, "length": 30},
    {"name": "QDD-400G-SR8-S", "speed": 400, "length": 100},
    {"name": "QDD-400G-SR4.2-BD", "speed": 400, "length": 150},
    {"name": "QDD-400G-ZR-S", "speed": 400, "length": 400},
    {"name": "QSFP-400G-DR4", "speed": 400, "length": 500},
    {"name": "QDD-400G-FR4-S", "speed": 400, "length": 2000},
    {"name": "QDD-400G-LR4-S", "speed": 400, "length": 10000},

    # 100G cables
    {"name": "QSFP-100G-CU1M", "speed": 100, "length": 1},
    {"name": "QSFP-100G-CU2M", "speed": 100, "length": 2},
    {"name": "QSFP-100G-CU3M", "speed": 100, "length": 3},
    {"name": "QSFP-100G-CU5M", "speed": 100, "length": 5},
    {"name": "QSFP-100G-AOC1M", "speed": 100, "length": 1},
    {"name": "QSFP-100G-AOC2M", "speed": 100, "length": 2},
    {"name": "QSFP-100G-AOC3M", "speed": 100, "length": 3},
    {"name": "QSFP-100G-AOC5M", "speed": 100, "length": 5},
    {"name": "QSFP-100G-AOC7M", "speed": 100, "length": 7},
    {"name": "QSFP-100G-AOC10M", "speed": 100, "length": 10},
    {"name": "QSFP-100G-AOC15M", "speed": 100, "length": 15},
    {"name": "QSFP-100G-AOC20M", "speed": 100, "length": 20},
    {"name": "QSFP-100G-AOC25M", "speed": 100, "length": 25},
    {"name": "QSFP-100G-AOC30M", "speed": 100, "length": 30},
    {"name": "QSFP-100G-SR4-S", "speed": 100, "length": 150},
    {"name": "QSFP-100G-DR-S", "speed": 100, "length": 500},
    {"name": "QSFP-100G-FR-S", "speed": 100, "length": 2000}
]
   
SUPPORTED_MODELS = ["HF6100-32D", "HF6100-60L4D"]

def _get_fabric(fabric_name):
    fabric_data_obj = {
        "fabric": {
            "name": fabric_name
        }
    }
    try:
        result = get_fabric(fabric_data_obj)
        if not result:
            logger.error(f"[AUTOCABLING] Fabric not found for: {fabric_name}")
            return None
        return result
    except Exception as e:
        logger.error(f"[AUTOCABLING] Error occurred while checking for fabric {fabric_name}: {e}", exc_info=True)
   
    return None

def _get_nodes(autocabling_data_obj):
    get_nodes_result = get_fabric_nodes(autocabling_data_obj)
    try:
        nodes = get_nodes_result.json()
    except json.decoder.JSONDecodeError as e:
        logger.error(f"Invalid JSON in response: {e}")
        nodes = None

    if not nodes:
        logger.warning(f"[AUTOCABLING] No nodes found in fabric: {autocabling_data_obj.get('fabric_id')}")
        return []
   
    return nodes.get("nodes") # The result is given as {'nodes': [...]}

def _get_fabric_connections(fabric_name):
    connections_data_obj = { # Function call expects an object
        "fabric_id": fabric_name,
    }
    try:
        connections = get_fabric_connections(connections_data_obj).json()
    except json.decoder.JSONDecodeError as e:
        logger.error(f"Invalid JSON in response: {e}")
        connections = None
   
    return connections.get("connections") # The result is given as {'connections': [...]}

def _analyze_existing_connections(connections, names_of_spine_nodes, is_spine_leaf_topo):
    if not connections:
        return set(), {}, [], [], []
   
    connection_set = set() # Set of tuples: (spine or leaf, leaf)
    occupied_ports = defaultdict(list) # nodeName -> list of occupied portNames
    existing_connections = [] # List of existing connections that should not be deleted
    redundant_connections = [] # List of connections that connect two already connected nodes
    connections_to_delete = [] # List of leaf-leaf connections. Will be empty if mesh topology
    for connection in connections:
        local_name = connection["local"]["nodeName"]
        remote_name = connection["remote"]["nodeName"]
        if is_spine_leaf_topo and local_name not in names_of_spine_nodes and remote_name not in names_of_spine_nodes: # leaf-leaf connections should be deleted in a spine-leaf topology
            connections_to_delete.append(connection)
        elif (remote_name, local_name) in connection_set or (local_name, remote_name) in connection_set:
            redundant_connections.append(connection)
        else:
            # Add both node names as a tuple to track existing connection
            connection_set.add((remote_name, local_name))
            existing_connections.append(connection)

        # Track which ports are used on each side
        occupied_ports[remote_name].append(connection["remote"]["portName"])
        occupied_ports[local_name].append(connection["local"]["portName"])
   
    if not is_spine_leaf_topo:
        connections_to_delete = [] # Enforce that this list is empty if mesh topology

    return connection_set, occupied_ports, redundant_connections, connections_to_delete, existing_connections

def _get_model_name(node):
    model_name = node.get("modelName")
    if not model_name or model_name not in SUPPORTED_MODELS:
        logger.warning(f"[AUTOCABLING] Node 'f{node.get('name')}' has an unsupported modelName: f{model_name}. Autocabling has been skipped for this node.")
    return model_name

def _get_next_available_port(node, occupied_ports):
    def loop_through(range):
        for idx in range:
            port = f"Ethernet1_{idx}"
            if port not in used_ports:
                if name not in occupied_ports: occupied_ports[name] = [port]
                else: occupied_ports[name].append(port)
                return port
           
        return None
           
    model_name = _get_model_name(node)
    name = node.get("name")

    port_range = range(1, 33) if model_name == "HF6100-32D" else range(31, 35)
    fallback_range = range(1, 65)
    used_ports = set(occupied_ports.get(name, []))  # convert to set for fast lookup

    port = loop_through(port_range)
    if port: return port
    else:    
        if model_name == "HF6100-60L4D":
            return loop_through(fallback_range)

    return None

def _connect_nodes(local_node, remote_node, occupied_ports):
    local_model_name, remote_model_name = _get_model_name(local_node), _get_model_name(remote_node)
    if local_model_name is None or remote_model_name is None:
        return

    local_port = _get_next_available_port(local_node, occupied_ports)
    remote_port = _get_next_available_port(remote_node, occupied_ports)

    if not local_port:
        logger.warning(f"[AUTOCABLING] No available port found for {local_node['name']}")
        return
    if not remote_port:
        logger.warning(f"[AUTOCABLING] No available port found for {remote_node['name']}")
        return

    new_connection = {
        "local": { # Leaf node
            "portName": local_port,
            "nodeName": local_node["name"]
        },
        "remote": { # Spine node
            "portName": remote_port,
            "nodeName": remote_node["name"]
        },
    }
    return new_connection

def _autocable_spine_leaf_topology(spine_nodes, leaf_nodes, pluggable, connection_set, occupied_ports):
    # Also check if it is being converted from mesh to spine-leaf, since you'll have to delete the leaf-leaf connections

    connections = []
    for spine in spine_nodes:
        for leaf in leaf_nodes:
            if ((leaf["name"], spine["name"]) in connection_set or (spine["name"], leaf["name"]) in connection_set): # Nodes are already connected
                continue

            new_connection = _connect_nodes(leaf, spine, occupied_ports)
            if new_connection:
                new_connection["pluggable"] = pluggable
                connections.append(new_connection)
   
    return connections

def _autocable_mesh_topology(nodes, pluggable, connection_set, occupied_ports):
    connections = []
    for i in range(0, len(nodes)):
        local_node = nodes[i]
        for j in range(i + 1, len(nodes)):
            remote_node = nodes[j]
            if ((local_node["name"], remote_node["name"]) in connection_set or (remote_node["name"], local_node["name"]) in connection_set): # Nodes are already connected
                continue

            new_connection = _connect_nodes(local_node, remote_node, occupied_ports)
            if new_connection:
                new_connection["pluggable"] = pluggable
                connections.append(new_connection)

    return connections

def select_cable(cables, speed, length):

    # Filter cables by speed
    matching_speed = [c for c in cables if c["speed"] == speed]

    # Find cable with exact matching length, or closest greater
    for cable in sorted(matching_speed, key=lambda c: c.get("length", float("inf"))):
        if "length" in cable and cable["length"] >= length:
            return cable["name"]

    raise ValueError(f"No suitable cable found for speed {speed} and length {length}")

def autocabling(autocabling_data_obj, pull_nodes_from_yaml=False):
    """
    Constructs a connections object with all leaves connected once to all spines (spine-leaf topology),
    or all leaves connected once to each other (mesh topology)

    Args:
        autocabling_data_obj (dict): An object containing the fabric name, an object for autocabling, and other potentially important attributes like nodes and connections
        pull_nodes_from_yaml (bool): If true, use the nodes and connections from autocabling_data_obj, otherwise pull directly from Hyperfabric
    Returns:
        connections (dict): Contains connections for autocabling, or None if an error occurs
    """    
    logger.info("[AUTOCABLING] Starting autocabling...")

    # Get nodes, either from provided yaml input or from the existing fabric in Hyperfabric
    if pull_nodes_from_yaml:
        result = _get_fabric(autocabling_data_obj["fabric_id"])
        # Inputting a yaml file to autocabling should only be done for fabrics that don't yet exist. Return if the fabric exists.
        if result is not None:
            logger.error(f"[AUTOCABLING] Fabric '{autocabling_data_obj['fabric_id']}' already exists. YAML file input to autocable.py is not supported for existing fabrics. Pass the fabric name instead.")
            return None

        nodes = autocabling_data_obj.get("nodes", [])
        connections = autocabling_data_obj.get("connections", [])
    else:
        result = _get_fabric(autocabling_data_obj["fabric_id"]) # Verify that fabric exists
        if result is None:
            logger.error(f"[AUTOCABLING] Fabric with name '{autocabling_data_obj['fabric_id']}' does not exist")
            return None
        nodes = _get_nodes(autocabling_data_obj)
        connections = _get_fabric_connections(autocabling_data_obj["fabric_id"])

    spine_nodes = []
    leaf_nodes = []
    names_of_spine_nodes = [] # Used to easily identify what is, or is not, a spine node

    for node in nodes:
        if node.get("roles")[0] == "SPINE":
            spine_nodes.append(node)
            names_of_spine_nodes.append(node["name"])
        elif node.get("roles")[0] == "LEAF":
            leaf_nodes.append(node)
        else:
            logger.warning(f"[AUTOCABLING] Unknown node type: expected type 'LEAF' or 'SPINE', but has role: {node.get('roles')}. Node will be excluded in autocabling.")
    connection_set, occupied_ports, redundant_connections, connections_to_delete, existing_connections = _analyze_existing_connections(connections, names_of_spine_nodes, len(spine_nodes) > 0)

    pluggable = autocabling_data_obj["autocabling_obj"].get("pluggable")
   
    if not pluggable:
        speed = autocabling_data_obj["autocabling_obj"].get("speed", 400)
        length = autocabling_data_obj["autocabling_obj"].get("length", 10)
        pluggable = select_cable(cables, speed, length)

    if len(spine_nodes) > 0:
        connections = _autocable_spine_leaf_topology(spine_nodes, leaf_nodes, pluggable, connection_set, occupied_ports)
    else:
        connections = _autocable_mesh_topology(leaf_nodes, pluggable, connection_set, occupied_ports)

    # Update pluggable for existing connections
    for conn in existing_connections:
        conn["pluggable"] = pluggable
   
    # Still update pluggable for connections we recommend to delete, in case the user chooses to keep them
    for conn in redundant_connections:
        conn["pluggable"] = pluggable
    for conn in connections_to_delete:
        conn["pluggable"] = pluggable
   
    return connections, redundant_connections, connections_to_delete, existing_connections