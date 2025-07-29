import logging
import requests
from pprint import pprint
from scripts.api_call_handler import handle_get, handle_delete, put_connections
from entities.registry import get_entity
from scripts.hyperfabric_api import get_fabric_connections, set_fabric_connections, delete_fabric_connection, get_management_ports
from scripts.autocabling import autocabling

# Setup logger
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

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

def _extract_connection_info(connections):
    return [
        {
            'id': conn['id'],
            'local': conn['local'],
            'remote': conn['remote'],
            'pluggable': conn.get('pluggable')
        }
        for conn in connections
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

def _delete_entity(key, objects, fabric_id):
    entity_obj = get_entity(key[:-1]) # key is plural, but the keys in get_entity are all singular
    if not entity_obj: return
    
    delete_func = entity_obj.get("func_obj").get("del_func")
    if not delete_func: return

    for obj in objects:
        data_obj = {
            "fabric_id": fabric_id,
            f"{key[:-1]}": obj
        }

        if key != "connections": # GET func in entity_obj for connections is None, so we don't want to return in that case
            get_func = entity_obj.get("func_obj").get("get_func")
            if not get_func: return
            
            # Call GET method to make sure object exists
            result = handle_get(get_func=get_func, post_func=None, put_func=None, delete_func=None, func_input=data_obj, key=key, clear_action_stack=True)
            if not isinstance(result, dict): # handle_get returns the object if found, otherwise a Response object 
                continue
        else:
            if "id" not in obj:
                logger.warning(f"[CONNECTIONS] [DELETE] Deleting connections is not supported without the connection ID")
                continue
        
        # DELETE endpoints for connections and VNIs require the object's ID, the endpoint for VRF requires a standard data_obj with "vrf" as a key and the object as its contents
        delete_obj = {
            "fabric_id": fabric_id,
            "id": obj.get("id") or obj.get("name"),
            f"{key[:-1]}": {
                "name": obj.get("name")
            }
        }

        # The DELETE endpoint for VNIs does not take a name (even though it should). So we must get its ID and replace the name.
        # Once this endpoint is fixed, the following code won't be necessary
        if key == "vnis":
            delete_obj["id"] = result.get("id")
            
        handle_delete(delete_func, delete_obj, key[:-1])

def _delete_connections(redundant_connections, leaf_connections, delete_connection_obj):
    print(f"Number of redundant connections to delete: {len(redundant_connections)}")
    for conn in redundant_connections:
        print(f"Connection between {conn['local']['nodeName']} on port {conn['local']['portName']} and {conn['remote']['nodeName']} on port {conn['remote']['portName']}")
    
    print(f"Number of leaf-leaf connections to delete: {len(leaf_connections)}")
    for conn in leaf_connections:
        print(f"Connection between {conn['local']['nodeName']} on port {conn['local']['portName']} and {conn['remote']['nodeName']} on port {conn['remote']['portName']}")
    
    connections_to_delete = redundant_connections + leaf_connections
    # Call _delete_entity instead?
    for del_conn in connections_to_delete:
        delete_connection_obj["id"] = del_conn.get("id")
        handle_delete(delete_fabric_connection, delete_connection_obj, "connection")

def _put_connections(fabric_id, connections):
    try:
        logger.info(f"[CONNECTION] [PUT] Making API request for all connections...")
        response = put_connections(fabric_id, connections, set_fabric_connections)
        response.raise_for_status()
    except Exception as e:
        raise EntityProcessingError(f"Error processing connections. Error: {response.json()}")

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
    
    """
    Attempts GET → if not found, POST → if found, PUT.
    Logs and prints final response object.
    Takes functions for GET, POST, PUT, then function input
    """
    result = handle_get(get_func=get_func, post_func=post_func, put_func=put_func, delete_func=del_func, key=key, func_input=data_object, clear_action_stack=reset_stack)
    if (result is not None and result.status_code == 200):
        logger.info(f"[{key.upper()}] [SUCCESS] created/updated successfully")
        print("=============================================================")
        return entity_other
    else:
        print("=============================================================")
        if result is not None:
            raise EntityProcessingError(f"Error processing a {key}. Error: {result.json()}")
        raise EntityProcessingError(f"Error processing a {key}. Erroneous entity: {entity}")

# Try to separate parts into a generic function
def _loop_through_attributes(fabric_other, FABRIC_ID):
    # -------------------- NODES --------------------
    if "nodes" in fabric_other:
        fabric_nodes = {"nodes": fabric_other["nodes"]}
        for i, node in enumerate(fabric_nodes["nodes"]):
            node_data_obj = {
                "fabric_id": FABRIC_ID
            }
            node_other = _process_entity(node, node_data_obj, "node", i == 0) # Reset action stack if first node

    # -------------------- MANAGEMENT PORTS --------------------
            if "managementPorts" in node_other:
                node_mgmt_ports = {"managementPorts": node_other["managementPorts"]}
                mgmt_port_data_obj = {
                    "fabric_id": FABRIC_ID,
                    "node_id": node["name"]
                }
                existing_mgmt_port = handle_get(get_func=get_management_ports, post_func=None, put_func=None, delete_func=None, func_input=mgmt_port_data_obj, key="mgmt_port")
                if existing_mgmt_port:
                    mgmt_port_data_obj["id"] = existing_mgmt_port["ports"][0]["name"]
                for mgmt_port in node_mgmt_ports["managementPorts"]:
                    mgmt_other = _process_entity(mgmt_port, mgmt_port_data_obj, "mgmt_port")

    # -------------------- PORTS --------------------
            if "ports" in node_other:
                node_ports = {"ports": node_other["ports"]}
                for port in node_ports["ports"]:
                    port_data_obj = {
                        "fabric_id": FABRIC_ID,
                        "node_id": node["name"]
                    }
                    port_other = _process_entity(port, port_data_obj, "port")

            _reset_latest_protected_key() # Reset at the end of processing a node

    # -------------------- AUTOCABLING --------------------
    # Autocabling, by default, enabled is assumed to be True if other attributes exist
    if "autocabling" in fabric_other and (fabric_other["autocabling"].get("enabled") is None or fabric_other["autocabling"].get("enabled") != False):
        autocabling_data_obj = {
            "fabric_id": FABRIC_ID,
            "autocabling_obj": fabric_other["autocabling"]
        }
        # auto_connections, redundant_connections, leaf_connections, existing_connections = autocabling(autocabling_data_obj)
        connections_result = autocabling(autocabling_data_obj)
        if connections_result is None:
            logger.error("Autocabling failed")
            return
        
        auto_connections, redundant_connections, leaf_connections, existing_connections = connections_result
        redundant_connections = _extract_connection_info(redundant_connections)
        leaf_connections = _extract_connection_info(leaf_connections)

        # Delete redundant connections, and any leaf-leaf connections if fabric is spine-leaf topology
        if len(redundant_connections) > 0 or len(leaf_connections) > 0:
            delete_connection_obj = {
                "fabric_id": FABRIC_ID
            }
            _delete_connections(redundant_connections, leaf_connections, delete_connection_obj)
        
        # Update existing connections
        new_connections = auto_connections + existing_connections
        _put_connections(FABRIC_ID, new_connections)

        if "connections" in fabric_other:
            logger.warning("[CONNECTIONS] Connections listed under 'connections' will be skipped as autocable is enabled")

    # -------------------- CONNECTIONS --------------------
    # only if autocabling was not enabled
    elif "connections" in fabric_other:
        fabric_connections = {"connections": fabric_other["connections"]}
        connection_data_obj = {
            "fabric_id": FABRIC_ID,
        }
        full_connections = handle_get(get_func=get_fabric_connections, post_func=None, put_func=None, delete_func=None, func_input=connection_data_obj, key="connection")
        current_connections = full_connections.get("connections", [])
        found_connections = set() # Set of connection IDs, referencing connections to be removed from current_connections

        # Loops through connections in YAML file.
        # If the connection exists in the fabric, append the id to found_connections so it can later be removed from current_connections
        # current_connections will contain the list of connections to be PUT, including old connections (not modified by new ones) and the new connections
        for connection in fabric_connections["connections"]:
            conn_id = _connection_exists(current_connections, connection) 
            if conn_id:
                found_connections.add(conn_id)
            current_connections.append(connection)
        
        current_connections = [conn for conn in current_connections if "id" not in conn or conn["id"] not in found_connections] # Remove duplicate connections
       
        _put_connections(FABRIC_ID, current_connections) # Update existing connections

    # -------------------- VNIs --------------------
    if "vnis" in fabric_other:
        fabric_vnis = {"vnis": fabric_other["vnis"]}
        for i, vni in enumerate(fabric_vnis["vnis"]):
            vni_data_obj = {
                "fabric_id": FABRIC_ID
            }
            vni_other = _process_entity(vni, vni_data_obj, "vni", i == 0) # Reset action stack if first VNI
            
            #Handle members?

            _reset_latest_protected_key() # Reset at the end of processing a VNI
    # -------------------- VRFs --------------------
    if "vrfs" in fabric_other:
        fabric_vrfs = {"vrfs": fabric_other["vrfs"]}
        for i, vrf in enumerate(fabric_vrfs["vrfs"]):
            vrf_data_obj = {
                "fabric_id": FABRIC_ID
            }
            vrf_other = _process_entity(vrf, vrf_data_obj, "vrf", i == 0) # Reset action stack if first VRF

    # -------------------- STATIC ROUTES --------------------
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
    
    # -------------------- OBJECT DELETION --------------------
    if "delete" in fabric_other:
        for key in fabric_other["delete"]:
            _delete_entity(key, fabric_other["delete"][key], FABRIC_ID)

def handle_json_input(json_input):
    FABRIC_ID = None

    successes = []
    failures = []

    for fabric in json_input["fabrics"]:
        if "name" in fabric:
            FABRIC_ID = fabric["name"]
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
                    logger.error(f"[FABRIC PROCESSING] Error while processing sub-entities for fabric '{FABRIC_ID}': {e}")
                    failures.append({"name": FABRIC_ID, "error": str(e)})
                    continue  # move to next fabric
            else:
                successes.append({"name": FABRIC_ID, "status": "Success"})

        except Exception as e:
            logger.error(f"[FABRIC PROCESSING] Exception at fabric level for fabric '{FABRIC_ID}': {e}", exc_info=True)
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

