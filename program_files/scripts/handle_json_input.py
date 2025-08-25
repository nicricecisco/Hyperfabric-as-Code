from pprint import pprint
from program_files.utils.logger import get_logger
from program_files.entities.registry import get_entity
from program_files.scripts.autocabling import autocabling
from program_files.scripts.api_call_handler import handle_get, handle_delete, put_connections, bind_devices
from program_files.scripts.hyperfabric_api import get_fabric_connections, set_fabric_connections, delete_fabric_connection, get_management_ports, bind_device, unbind_device

# Setup logger
logger = get_logger()

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

            # Add attributes from existing conn to yaml conn if the attribute does not exist
            for attr in conn:
                if attr not in target_connection:
                    target_connection[attr] = conn[attr]

            # Remove existing conn from list to call PUT with, but add the current yaml conn
            connections.remove(conn)
            connections.append(target_connection)
            
            return conn.get('id', {})  # Match found, return id of connection

    return None  # No match, no id

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
    
def _restructure_annotations(annotations):
    return [{"name": k, "value": v} for k, v in annotations.items()]
    
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
    
    # Split the object into "pure" and "other" attributes
    # Pure attributes are ones that get sent directly to the API to configure that object
    # Other attributes are ones that may need to get iterated over and processed themselves (ex. nodes under a fabric, or ports under a node)
    entity_pure, entity_other = _parse_attributes(entity, attributes)
    data_object[key] = entity_pure

    # Restructure annotations, if any
    if "annotations" in entity_pure:
        entity_pure["annotations"] = _restructure_annotations(entity_pure["annotations"])

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
        for i, node in enumerate(fabric_other["nodes"]):
            node_data_obj = {
                "fabric_id": FABRIC_ID
            }
            node_other = _process_entity(node, node_data_obj, "node", i == 0) # Reset action stack if first node

    # -------------------- MANAGEMENT PORTS --------------------
            if "managementPorts" in node_other:
                mgmt_port_data_obj = {
                    "fabric_id": FABRIC_ID,
                    "node_id": node["name"]
                }
                existing_mgmt_port = handle_get(get_func=get_management_ports, post_func=None, put_func=None, delete_func=None, func_input=mgmt_port_data_obj, key="mgmt_port")
                if existing_mgmt_port:
                    mgmt_port_data_obj["id"] = existing_mgmt_port["ports"][0]["name"]
                for mgmt_port in node_other["managementPorts"]:
                    mgmt_other = _process_entity(mgmt_port, mgmt_port_data_obj, "mgmt_port")

    # -------------------- PORTS --------------------
            if "ports" in node_other:
                for port in node_other["ports"]:
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
        connection_data_obj = {
            "fabric_id": FABRIC_ID,
        }
        full_connections = handle_get(get_func=get_fabric_connections, post_func=None, put_func=None, delete_func=None, func_input=connection_data_obj, key="connection")
        current_connections = full_connections.get("connections", [])

        # Loops through connections in YAML file.
        # current_connections will contain the list of connections to be PUT, including old connections (not modified by new ones) and the new connections
        for connection in fabric_other["connections"]:
            conn_id = _connection_exists(current_connections, connection) # Adds current connection to list of connections to PUT, if found
            if not conn_id:
                current_connections.append(connection) # Add new connection to list of connections to PUT
               
        _put_connections(FABRIC_ID, current_connections) # Update existing connections

    # -------------------- VNIs --------------------
    if "vnis" in fabric_other:
        for i, vni in enumerate(fabric_other["vnis"]):
            vni_data_obj = {
                "fabric_id": FABRIC_ID
            }
            vni_other = _process_entity(vni, vni_data_obj, "vni", i == 0) # Reset action stack if first VNI
            
            #Handle members?

            _reset_latest_protected_key() # Reset at the end of processing a VNI

    # -------------------- VRFs --------------------
    if "vrfs" in fabric_other:
        for i, vrf in enumerate(fabric_other["vrfs"]):
            vrf_data_obj = {
                "fabric_id": FABRIC_ID
            }
            vrf_other = _process_entity(vrf, vrf_data_obj, "vrf", i == 0) # Reset action stack if first VRF

    # -------------------- STATIC ROUTES --------------------
            if "staticRoutes" in vrf_other:
                for static_route in vrf_other["staticRoutes"]:
                    static_route_data_obj = {
                        "fabric_id": FABRIC_ID,
                        "vrf_id": vrf["name"],
                    }
                    static_route_other = _process_entity(static_route, static_route_data_obj, "static_route")
            
            _reset_latest_protected_key() # Reset at the end of processing a VRF

    # -------------------- BINDING --------------------
    if "bind" in fabric_other:
        bind_func_obj = {
            "bind": bind_device,
            "unbind": unbind_device
        }
        failed_bindings = []
        for i, bind_obj in enumerate(fabric_other["bind"]):
            bind_data_obj = {
                "fabric_id": FABRIC_ID,
                "node_id": bind_obj.get("nodeName"),
                "device_id": bind_obj.get("deviceId")
            }
            result = bind_devices(bind_data_obj, bind_func_obj) 
            if result is not None and result.status_code != 200:
                failed_bindings.append((bind_obj, result.json()))
        
        if (len(failed_bindings) == 0):
            logger.info("[BINDING] [SUCCESS] devices bound successfully")
            print("=============================================================")
        else:
            print("=============================================================")
            for failed_bind_obj, error in failed_bindings:
                logger.error(f"[BINDING] Failed to bind device '{failed_bind_obj.get('deviceId')}' to node '{failed_bind_obj.get('nodeName')}'. Error: {error}")
            print("=============================================================")
            raise EntityProcessingError(f"Error binding. See the above messages for specific errors.")
    
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

