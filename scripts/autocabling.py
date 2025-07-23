import json
import logging
from pprint import pprint
from collections import defaultdict
from scripts.hyperfabric_api import get_fabric_nodes, get_fabric_connections

# Setup logger
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_PLUGGABLE = "QDD-2Q200-CU3M"
SUPPORTED_MODELS = ["HF6100-32D", "HF6100-60L4D"]

# For next week:
# Don't duplicate already existing connections. You have to update the pluggable value.
# Figure out a way to get the next available port in this case

# Plan:
# Have this accessible from the main pipeline, but also allow a new pipeline to access this and output just the connections in YAML format

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

def _analyze_existing_connections(connections):
    if not connections:
        return set(), {}, []
    
    connection_set = set() # Set of tuples: (spine or leaf, leaf) 
    occupied_ports = defaultdict(list) # nodeName -> list of occupied portNames
    redundant_connections = [] # List of connections with 
    for connection in connections:
        if (connection["remote"]["nodeName"], connection["local"]["nodeName"]) in connection_set or (connection["local"]["nodeName"], connection["remote"]["nodeName"]) in connection_set:
            redundant_connections.append(connection)
        else:
            # Add both node names as a tuple to track existing connection
            connection_set.add((connection["remote"]["nodeName"], connection["local"]["nodeName"]))

        # Track which ports are used on each side
        occupied_ports[connection["remote"]["nodeName"]].append(connection["remote"]["portName"])
        occupied_ports[connection["local"]["nodeName"]].append(connection["local"]["portName"])

    print("PRINTING REDUNDANT CONNECTIONS...")
    pprint(redundant_connections)

    print("PRINTING OCCUPIED PORTS...")
    pprint(occupied_ports)

    return connection_set, occupied_ports, redundant_connections

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
    
    print("PRINTING NEW CONNECTIONS...")
    pprint(connections)
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

    print("PRINTING NEW CONNECTIONS...")
    pprint(connections)
    return connections

def autocabling(autocabling_data_obj, pull_nodes_from_yaml=False):
    """
    Constructs a connections object with all leaves connected once to all spines (spine-leaf topology), 
    or all leaves connected once to each other (mesh topology)

    Args:
        autocabling_data_obj (dict): An object containing the fabric name, an object for autocabling, and other potentially other attributes like nodes and connections
        pull_nodes_from_yaml (bool): If true, use the nodes and connections from autocabling_data_obj, otherwise pull directly from Hyperfabric
    Returns:
        connections (dict): Contains connections for autocabling
    """     
    logger.info("[AUTOCABLING] Starting autocabling...")
    # Get nodes, either from provided yaml input or from the existing fabric in Hyperfabric
    if pull_nodes_from_yaml:
        nodes = autocabling_data_obj.get("nodes", [])
        connections = autocabling_data_obj.get("connections", [])
    else:
        nodes = _get_nodes(autocabling_data_obj)
        connections = _get_fabric_connections(autocabling_data_obj["fabric_id"])

    spine_nodes = []
    leaf_nodes = []

    for node in nodes:
        if node.get("roles")[0] == "SPINE":
            spine_nodes.append(node)
        elif node.get("roles")[0] == "LEAF":
            leaf_nodes.append(node)
        else:
            logger.warning(f"[AUTOCABLING] Unknown node type: expected type 'LEAF' or 'SPINE', but has role: {node.get('roles')}. Node will be excluded in autocabling.")

    connection_set, occupied_ports, redundant_connections = _analyze_existing_connections(connections)
    # Don't overwrite port connections, but do overwrite cable

    pluggable = autocabling_data_obj["autocabling_obj"].get("pluggable")
    if not pluggable:
        pluggable = DEFAULT_PLUGGABLE

    if len(spine_nodes) > 0:
        connections = _autocable_spine_leaf_topology(spine_nodes, leaf_nodes, pluggable, connection_set, occupied_ports)
    else:
        connections = _autocable_mesh_topology(leaf_nodes, pluggable, connection_set, occupied_ports)

    # Undo overwriting here? Maybe??

    return connections