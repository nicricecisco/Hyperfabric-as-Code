from pprint import pprint
from scripts.api_call_handler import handle_get
from entities.registry import get_entity
from scripts.hyperfabric_api import get_fabric_connections, get_management_ports
from scripts.autocabling import autocabling

class EntityProcessingError(Exception):
    pass

class ProtectedKey:
    def __init__(self, type):
        self.active = False
        self.type = type

LATEST_PROTECTED_KEY = None

def _reset_latest_protected_key():
    global LATEST_PROTECTED_KEY
    if LATEST_PROTECTED_KEY:
        LATEST_PROTECTED_KEY.active = True
        LATEST_PROTECTED_KEY = None

def _parse_attributes(obj, attributes):
    pure = {key: obj[key] for key in obj if key in attributes}
    other = {key: obj[key] for key in obj if key not in attributes}

    return pure, other

def _extract_connection_info(connections_data):
    return [
        {
            'id': conn['id'],
            'local': conn['local'],
            'remote': conn['remote']
        }
        for conn in connections_data.get('connections', [])
    ]

def _connection_exists(connections, target_connection):
    target_local = target_connection.get('local', {})
    target_remote = target_connection.get('remote', {})

    for conn in connections:
        local = conn.get('local', {})
        remote = conn.get('remote', {})

        if (local.get('nodeName') == target_local.get('nodeName') and
            local.get('portName') == target_local.get('portName') and
            remote.get('nodeName') == target_remote.get('nodeName') and
            remote.get('portName') == target_remote.get('portName')):
            return conn.get('id', {})  # Match found, return id of connection

    return None  # No match, no id

def _process_entity(entity, data_object, key, reset_stack=False):
    """
    Submits entity to Hyperfabric Cloud Controller

    Args:
        entity (dict): An entity like a fabric, node, port, etc with its associated attributes
        data_object (dict): The metadata and data necessary for sending it to Hyperfabric
        key (str): The name of the entity (like 'fabric' or 'node')
        reset_stack (bool): If true, reset the stack of actions for rollbacks
    Returns:
        entity_other (dict): Child attributes of entity that must be further processed or discarded
    """        
    global LATEST_PROTECTED_KEY

    entity_obj = get_entity(key)
    attributes, func_obj = entity_obj.get("attributes"), entity_obj.get("func_obj")
    get_func, post_func, put_func, del_func = func_obj.get("get_func"), func_obj.get("post_func"), func_obj.get("put_func"), func_obj.get("del_func")
    
    entity_pure, entity_other = _parse_attributes(entity, attributes)
    data_object[key] = entity_pure

    if entity_pure.pop("protected", False):
        protected_key = ProtectedKey(key)
        data_object["protected"] = protected_key
        LATEST_PROTECTED_KEY = protected_key
    elif LATEST_PROTECTED_KEY:
        data_object["protected"] = LATEST_PROTECTED_KEY

    pprint(entity_pure)
    print(data_object.get("protected"))
    
    """
    Attempts GET → if not found, POST → if found, PUT.
    Logs and prints final response object.
    Takes functions for GET, POST, PUT, then function input
    """
    result = handle_get(get_func=get_func, post_func=post_func, put_func=put_func, delete_func=del_func, key=key, func_input=data_object, clear_action_stack=reset_stack)
    print(result)
    if (result is not None and result.status_code == 200):
        print(f"{key} result: Success!")
        return entity_other
    else:
        if result is not None:
            raise EntityProcessingError(f"Error processing a {key}. Error: {result.json()}")
        raise EntityProcessingError(f"Error processing a {key}. Erroneous entity: {entity}")

# Try to separate parts into a generic function
def _loop_through_attributes(fabric_other, FABRIC_ID):
    # Nodes
    if "nodes" in fabric_other:
        fabric_nodes = {"nodes": fabric_other["nodes"]}
        for i, node in enumerate(fabric_nodes["nodes"]):
            node_data_obj = {
                "fabric_id": FABRIC_ID
            }
            node_other = _process_entity(node, node_data_obj, "node", i == 0) # Reset action stack if first node

    # Management ports
            if "managementPorts" in node_other:
                node_mgmt_ports = {"managementPorts": node_other["managementPorts"]}
                mgmt_port_data_obj = {
                    "fabric_id": FABRIC_ID,
                    "node_id": node["name"]
                }
                existing_mgmt_port = handle_get(get_func=get_management_ports, post_func=None, put_func=None, delete_func=None, func_input=mgmt_port_data_obj, key="mgmt_port")
                if existing_mgmt_port:
                    mgmt_port_data_obj["id"] = existing_mgmt_port["ports"][0]["name"]
                    print("MGMT PORT ID:", mgmt_port_data_obj["id"])
                for mgmt_port in node_mgmt_ports["managementPorts"]:
                    mgmt_other = _process_entity(mgmt_port, mgmt_port_data_obj, "mgmt_port")

    # Ports
            if "ports" in node_other:
                node_ports = {"ports": node_other["ports"]}
                for port in node_ports["ports"]:
                    port_data_obj = {
                        "fabric_id": FABRIC_ID,
                        "node_id": node["name"]
                    }
                    port_other = _process_entity(port, port_data_obj, "port")

            _reset_latest_protected_key() # Reset at the end of processing a node

    # Autocabling, by default, enabled is assumed to be True if other attributes exist
    if "autocabling" in fabric_other and (fabric_other["autocabling"].get("enabled") is None or fabric_other["autocabling"].get("enabled") != False):
        autocabling_data_obj = {
            "fabric_id": FABRIC_ID,
            "autocabling_obj": fabric_other["autocabling"]
        }
        auto_connections = autocabling(autocabling_data_obj)

        for i, connection in enumerate(auto_connections):
            _process_entity(connection, autocabling_data_obj, "connection", i == 0) # Reset action stack if first connection

    # Connections, only if autocabling was not enabled
    elif "connections" in fabric_other:
        fabric_connections = {"connections": fabric_other["connections"]}
        connection_data_obj = {
            "fabric_id": FABRIC_ID,
        }
        full_connections = handle_get(get_func=get_fabric_connections, post_func=None, put_func=None, delete_func=None, func_input=connection_data_obj, key="connection")
        current_connections = _extract_connection_info(full_connections)
        for i, connection in enumerate(fabric_connections["connections"]):
            conn_id = _connection_exists(current_connections, connection) 
            if (conn_id is None): # If connection does not exist, call POST 
                connection_other = _process_entity(connection, connection_data_obj, "connection", i == 0) # Reset action stack if first connection

            _reset_latest_protected_key() # Reset at the end of processing a connection

    # VNIs
    if "vnis" in fabric_other:
        fabric_vnis = {"vnis": fabric_other["vnis"]}
        for i, vni in enumerate(fabric_vnis["vnis"]):
            vni_data_obj = {
                "fabric_id": FABRIC_ID
            }
            vni_other = _process_entity(vni, vni_data_obj, "vni", i == 0) # Reset action stack if first VNI
            
            #Handle members?

            _reset_latest_protected_key() # Reset at the end of processing a VNI
    #VRFs
    if "vrfs" in fabric_other:
        fabric_vrfs = {"vrfs": fabric_other["vrfs"]}
        for i, vrf in enumerate(fabric_vrfs["vrfs"]):
            vrf_data_obj = {
                "fabric_id": FABRIC_ID
            }
            vrf_other = _process_entity(vrf, vrf_data_obj, "vrf", i == 0) # Reset action stack if first VRF

    # Static Routes
            if "staticRoutes" in vrf_other:
                static_routes = {"staticRoutes": vrf_other["staticRoutes"]}
                for static_route in static_routes["staticRoutes"]:
                    # Pure/Other is not required, but maybe it would be a good idea to include once we get the schema anyways
                    static_route_data_obj = {
                        "fabric_id": FABRIC_ID,
                        "vrf_id": vrf["name"],
                    }
                    static_route_other = _process_entity(static_route, static_route_data_obj, "static_route")
            
            _reset_latest_protected_key() # Reset at the end of processing a VRF

def handle_json_input(json_input):
    FABRIC_ID = None
    # Validate schema first
    if "fabrics" not in json_input:
        pprint("Input missing 'fabrics' attribute")
        return
    if not isinstance(json_input["fabrics"], list):
        pprint("'fabrics' attribute must contain a list")
        return
    
    successes = []
    failures = []

    for fabric in json_input["fabrics"]:
        if "name" in fabric:
            FABRIC_ID = fabric["name"]
            print("FABRIC_ID:", FABRIC_ID)
        else:
            FABRIC_ID = "UNKNOWN"

        try:
            fabric_data_obj = {}
            fabric_other = _process_entity(fabric, fabric_data_obj, "fabric", True)

            if fabric_other and len(fabric_other) > 0:
                try:
                    _loop_through_attributes(fabric_other, FABRIC_ID)
                    successes.append({"name": FABRIC_ID, "status": "Success"})
                except EntityProcessingError as e:
                    print(f"Error while processing sub-entities for fabric '{FABRIC_ID}': {e}")
                    failures.append({"name": FABRIC_ID, "error": str(e)})
                    continue  # move to next fabric
            else:
                successes.append({"name": FABRIC_ID, "status": "Success"})

        except Exception as e:
            print(f"Exception at fabric level for fabric '{FABRIC_ID}': {e}")
            failures.append({"name": FABRIC_ID, "error": str(e)})
            continue

    status = (
        "success" if not failures else
        "failure" if not successes else
        "partial_success"
    )

    return {
        "status": status,
        "summary": {"succeeded": len(successes), "failed": len(failures)},
        "results": {"successes": successes, "failures": failures}
    }

