from pprint import pprint
from scripts.api_call_handler import handle_get
from scripts.hyperfabric_api import get_fabric, create_fabric, update_fabric, \
    get_fabric_node, add_fabric_nodes, update_fabric_node, \
    get_management_port, add_management_ports, update_management_port, \
    get_port, update_port, \
    get_fabric_connections, get_fabric_connection, add_fabric_connections, set_fabric_connections

def _parse_fabric_attributes(fabric):
    # Pull this from an official schema?
    fabric_attributes = ["name", "address", "city", "country", "description", "location", "topology", "labels", "annotations"]
    fabric_pure = {key: fabric[key] for key in fabric if key in fabric_attributes}
    fabric_other = {key: fabric[key] for key in fabric if key not in fabric_attributes}

    return fabric_pure, fabric_other

def _parse_node_attributes(node):
    # Pull this from an official schema?
    node_attributes = ["name", "roles", "modelName", "location", "description", "serialNumber", "labels", "psuAirflows"]
    node_pure = {key: node[key] for key in node if key in node_attributes}
    node_other = {key: node[key] for key in node if key not in node_attributes}

    return node_pure, node_other

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

def _loop_through_attributes(fabric_other, FABRIC_ID):
    # Nodes
    if "nodes" in fabric_other:
        fabric_nodes = {"nodes": fabric_other["nodes"]}
        for node in fabric_nodes["nodes"]:
            pprint(node)
            node_pure, node_other = _parse_node_attributes(node)
            node_data_obj = {
                "fabric_id": FABRIC_ID,
                "node": node_pure
            }
            result_node = handle_get(get_fabric_node, add_fabric_nodes, update_fabric_node, node_data_obj)
            print("Node result:")
            pprint(result_node)

            # Management ports
            if "managementPorts" in node_other:
                node_mgmt_ports = {"managementPorts": node_other["managementPorts"]}
                for mgmt_port in node_mgmt_ports["managementPorts"]:
                    # Pure/Other is not required, but maybe it would be a good idea to include once we get the schema anyways
                    pprint(mgmt_port)
                    mgmt_port_data_obj = {
                        "fabric_id": FABRIC_ID,
                        "node_id": node_pure["name"],
                        "mgmt_port": mgmt_port
                    }
                    result_mgmt_port = handle_get(get_management_port, add_management_ports, update_management_port, mgmt_port_data_obj)
                    print("Management port result: ")
                    pprint(result_mgmt_port)

            # Ports
            if "ports" in node_other:
                node_ports = {"ports": node_other["ports"]}
                for port in node_ports["ports"]:
                    # Pure/Other is not required, but maybe it would be a good idea to include once we get the schema anyways
                    pprint(port)
                    port_data_obj = {
                        "fabric_id": FABRIC_ID,
                        "node_id": node_pure["name"],
                        "port": port
                    }
                    result_port = handle_get(get_port, None, update_port, port_data_obj)
                    pprint(result_port)
    if "connections" in fabric_other:
        fabric_connections = {"connections": fabric_other["connections"]}
        connection_data_obj = {
            "fabric_id": FABRIC_ID,
        }
        full_connections = handle_get(get_fabric_connections, None, None, connection_data_obj)
        current_connections = _extract_connection_info(full_connections)
        for connection in fabric_connections["connections"]:
            # Pure/Other is not required, but maybe it would be a good idea to include once we get the schema anyways
            conn_id = _connection_exists(current_connections, connection)
            print(conn_id)
            if (conn_id is None):
                connection_data_obj["connection"] = connection
                connection_data_obj["connection_id"] = conn_id
                print(connection)
                result_connection = handle_get(None, add_fabric_connections, None, connection_data_obj)
                pprint(result_connection)
            
                    

def handle_json_input(json_input):
    FABRIC_ID = None
    # Validate schema first
    if "fabrics" not in json_input:
        pprint("Input missing 'fabrics' attribute")
        return
    if not isinstance(json_input["fabrics"], list):
        pprint("'fabrics' attribute must contain a list")
        return
    if "name" in json_input["fabrics"][0]:
        FABRIC_ID = json_input["fabrics"][0]["name"]
        print("FABRIC_ID: ", FABRIC_ID)

    # Split fabric attributes
    fabric_pure, fabric_other = _parse_fabric_attributes(json_input["fabrics"][0])

    """
    Attempts GET → if not found, POST → if found, PUT.
    Logs and prints final response object.
    Takes functions for GET, POST, PUT, then function input
    """
    response = handle_get(get_fabric, create_fabric, update_fabric, fabric_pure)
    pprint(response)

    # Handle sub-fabric attributes
    _loop_through_attributes(fabric_other, FABRIC_ID)


