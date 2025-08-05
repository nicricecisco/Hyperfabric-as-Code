import requests, json
from pprint import pprint
from utils.load_token import load_token

BASE_URL = "https://hyperfabric.cisco.com/api/v1"
TOKEN = load_token()

headers = {
  "Content-Type": "application/json",
  "Accept": "application/json",
  "Authorization": f"Bearer {TOKEN}",
}

def _make_get_request(headers, url, params=None):
    return requests.get(url, headers=headers, params=params)
        
def _make_put_request(headers, url, payload=None):
    return requests.put(url, headers=headers, json=payload)
    
def _make_post_request(headers, url, payload=None):
    return requests.post(url, headers=headers, json=payload)

def _make_delete_request(headers, url):
    return requests.delete(url, headers=headers)


# ------------------------------ FABRICS ------------------------------

    
# /fabrics
def create_fabric(fabric_data_obj):
    """
    Creates a new fabric.
    Args:
        fabric_data_obj (dict): A dictionary containing the fabric specification.
            Must include the fabric definition under fabric_data_obj["fabric"].

    Returns:
        dict: The JSON response containing the created fabric information, or None if the request fails.
    """

    payload = {"fabrics": [fabric_data_obj["fabric"]]}
    url = f"{BASE_URL}/fabrics"
    response = _make_post_request(headers, url, payload=payload)

    return response

# /fabrics/{fabricId}
def get_fabric(fabric_data_obj):
    """
    Retrieves a specific fabric.
    Args:
        fabric_data_obj (dict): A dictionary containing fabric configuration details. 
            Must include the fabric name under fabric_data_obj["fabric"]["name"].
            Optional keys include:
              - "candidate": The candidate configuration name.
              - "includeMetadata": Whether to include object metadata in the response.

    Returns:
        dict: The JSON response containing the fabric information, or None if the request fails.
    """
    params = {key: fabric_data_obj["fabric"][key] for key in ["candidate", "includeMetadata"] if key in fabric_data_obj["fabric"]}
    fabricId = fabric_data_obj["fabric"]["name"]
    response = _make_get_request(headers, f"{BASE_URL}/fabrics/{fabricId}", params=params)
    return response

def update_fabric(fabric_data_obj):
    """
    Updates a specific fabric.

    Args:
        fabric_data_obj (dict): A dictionary containing the fabric data. Expected keys:
            - "fabric" (dict): A dictionary containing the updated fabric properties.
              Example:
              ```json
              {
                "name": "updated-fabric-name",
                "description": "Updated fabric description",
                "location": "Updated Location",
                "address": "Updated Address",
                "city": "Updated City",
                "country": "US",
                "labels": ["label1", "label2"],
                "topology": "SPINE_LEAF"
              }
              ```

    Returns:
        dict: JSON response containing the updated fabric information, or None on error.
    """
    fabricId = fabric_data_obj["fabric"]["name"]
    response = _make_put_request(headers, f"{BASE_URL}/fabrics/{fabricId}", payload=fabric_data_obj["fabric"])
    return response

def delete_fabric(fabric_data_obj):
    """
    Deletes a specific fabric.
    Args:
        fabric_data_obj (dict): A dictionary containing the fabric data. Expected keys:
            - "fabric" (dict): A dictionary containing the fabric's name.
              Example: {"fabric": {"name": "fabric-to-delete"}}
    Returns:
        int: HTTP status code, or None on error.
    """
    fabricId = fabric_data_obj["fabric"]["name"]
    response = _make_delete_request(headers, f"{BASE_URL}/fabrics/{fabricId}")
    return response


# ------------------------------ NODES ------------------------------


# /fabrics/{fabricId}/nodes
def get_fabric_nodes(autocabling_data_obj):
    """
    Retrieves a list of nodes within a fabric.

    Args:
        autocabling_data_obj (dict): A dictionary containing the fabric ID and optional parameters. Expected keys:
            - "fabric_id" (str): The ID or name of the fabric.
            - "autocabling_obj" (dict, optional): A dictionary containing query parameters.
              Expected sub-keys:
                - "candidate" (str, optional): The candidate configuration name. Defaults to None.
                - "includeMetadata" (bool, optional): Include object metadata in the response. Defaults to False.

    Returns:
        dict: JSON response, or None on error.
    """

    params = {key: autocabling_data_obj["autocabling_obj"][key] for key in ["candidate", "includeMetadata"] if "autocabling_obj" in autocabling_data_obj and key in autocabling_data_obj["autocabling_obj"]}
    fabricId = autocabling_data_obj["fabric_id"]
    response = _make_get_request(headers, f"{BASE_URL}/fabrics/{fabricId}/nodes", params=params)
    return response

# /fabrics/{fabricId}/nodes/{nodeId}
def get_fabric_node(node_data_obj):
    """
    Retrieves a specific node by ID or name.

    Args:
        node_data_obj (dict): A dictionary containing the fabric and node IDs, and optional parameters. Expected keys:
            - "fabric_id" (str): The ID or name of the fabric.
            - "node" (dict): A dictionary containing the node's name and optional query parameters.
              Expected sub-keys:
                - "name" (str): The ID or name of the node.
                - "candidate" (str, optional): The candidate configuration name. Defaults to None.
                - "includeMetadata" (bool, optional): Include object metadata in the response. Defaults to False.

    Returns:
        dict: JSON response, or None on error.
    """
    params = {key: node_data_obj["node"][key] for key in ["candidate", "includeMetadata"] if key in node_data_obj["node"]}
    fabricId = node_data_obj["fabric_id"]
    nodeId = node_data_obj["node"]["name"]
    response = _make_get_request(headers, f"{BASE_URL}/fabrics/{fabricId}/nodes/{nodeId}", params=params)
    return response

def add_fabric_nodes(node_data_obj):
    """
    Adds one or more nodes to a fabric.

    Args:
        node_data_obj (dict): A dictionary containing the fabric ID and node data. Expected keys:
            - "fabric_id" (str): The ID or name of the fabric.
            - "node" (dict): A dictionary representing a single node object to add.
              Example:
              ```json
              {
               "name": "node-leaf0",
               "description": "example fabric node leaf zero",
               "enabled": true,
               "serialNumber": "RESTAA2000",
               "modelName": "HF6100-60L4D",
               "roles": [
                "LEAF"
               ],
               "labels": [
                "TAG_ONE_ZERO"
               ]
              }
              ```
              Note: The function wraps this single node in a list for the API call.

    Returns:
        dict: JSON response, or None on error.
    """
    fabric_name = node_data_obj["fabric_id"]
    payload = {"nodes": [node_data_obj["node"]]}
    response = _make_post_request(headers, f"{BASE_URL}/fabrics/{fabric_name}/nodes", payload=payload)
    return response

def update_fabric_node(node_data_obj):
    """
    Updates a specific node.

    Args:
        node_data_obj (dict): A dictionary containing the fabric ID, node ID, and updated node properties. Expected keys:
            - "fabric_id" (str): The ID or name of the fabric.
            - "node" (dict): A dictionary containing the updated node properties. Must include "name" for node ID.
              Example:
              ```json
              {
                "name": "node-leaf0",
                "description": "Updated description",
                "enabled": true
              }
              ```

    Returns:
        dict: JSON response, or None on error.
    """
    fabricId = node_data_obj["fabric_id"]
    nodeId = node_data_obj["node"]["name"]
    node_data_obj["node"]["enabled"] = True # Enabled must be an attribute and it must be set to true
    # node_data_obj["node"]["osType"] = "HYPER_FABRIC"
    payload = node_data_obj["node"]
    response = _make_put_request(headers, f"{BASE_URL}/fabrics/{fabricId}/nodes/{nodeId}", payload=payload)
    return response

def delete_fabric_node(node_data_obj):
    """
    Deletes a specific node.

    Args:
        node_data_obj (dict): A dictionary containing the fabric ID and node ID. Expected keys:
            - "fabric_id" (str): The ID or name of the fabric.
            - "node" (dict): A dictionary containing the node's name.
              Example: {"node": {"name": "node-to-delete"}}

    Returns:
        dict: JSON response
    """
    fabricId = node_data_obj["fabric_id"]
    nodeId = node_data_obj["node"]["name"]
    response = _make_delete_request(headers, f"{BASE_URL}/fabrics/{fabricId}/nodes/{nodeId}")
    return response


# ------------------------------ MANAGEMENT PORTS ------------------------------


# /fabrics/{fabricId}/nodes/{nodeId}/managementPorts
def get_management_ports(mgmt_port_data_obj):
    """
    Retrieves a list of management ports for a specific node.
    Args:
        mgmt_port_data_obj (dict): A dictionary containing fabric ID, node ID, and optional parameters. Expected keys:
            - "fabric_id" (str): The ID or name of the fabric.
            - "node_id" (str): The ID or name of the node.
            - "mgmt_port" (dict, optional): A dictionary containing query parameters.
              Expected sub-keys:
                - "candidate" (str, optional): The candidate configuration name. Defaults to None.
                - "includeMetadata" (bool, optional): Include object metadata in the response. Defaults to False.
    Returns:
        dict: JSON response containing the list of management ports, or None on error.
    """
    params = {key: mgmt_port_data_obj["mgmt_port"][key] for key in ["candidate", "includeMetadata"] if "mgmt_port" in mgmt_port_data_obj and key in mgmt_port_data_obj["mgmt_port"]}
    fabricId = mgmt_port_data_obj["fabric_id"]
    nodeId = mgmt_port_data_obj["node_id"]
    response = _make_get_request(headers, f"{BASE_URL}/fabrics/{fabricId}/nodes/{nodeId}/managementPorts", params=params)
    return response

# /fabrics/{fabricId}/nodes/{nodeId}/managementPorts/{id}
def get_management_port(mgmt_port_data_obj):
    """
    Retrieves information on the management port specified

    Args:
        mgmt_port_data_obj (dict): A dictionary containing fabric ID, node ID, and port identifier. Expected keys:
            - "fabric_id" (str): The ID or name of the fabric.
            - "node_id" (str): The node id or name from which a device is bound.
            - "mgmt_port" (dict): A dictionary which may contain the "name" of the port if "id" is not provided.
            - "id" (str, optional): ID of the port. If not provided, it attempts to use `mgmt_port["name"]` or defaults to "eth0".
            
    Returns:
        dict: JSON response
    """
    fabricId = mgmt_port_data_obj["fabric_id"]
    nodeId = mgmt_port_data_obj["node_id"]
    if "id" in mgmt_port_data_obj:
      id = mgmt_port_data_obj["id"]
    else:
      if "name" not in mgmt_port_data_obj["mgmt_port"]:
        id = "eth0"
      else:
        id = mgmt_port_data_obj["mgmt_port"]["name"]
    response = _make_get_request(headers, f"{BASE_URL}/fabrics/{fabricId}/nodes/{nodeId}/managementPorts/{id}")
    return response

def add_management_ports(mgmt_port_data_obj):
    """
    Creates or updates one or more ManagementPorts for a fabric node

    Args:
        mgmt_port_data_obj (dict): A dictionary containing fabric ID, node ID, and management port data. Expected keys:
            - "fabric_id" (str): The ID or name of the fabric.
            - "node_id" (str): The node id or name from which a device is bound.
            - "mgmt_port" (dict): A dictionary representing a single management port to add/update.
              Example payload for "mgmt_port":
              ```json
               {
                "name": "eth0",
                "ipv4Address": "10.1.1.250/31",
                "ipv4Gateway": "10.1.1.251",
                "dnsAddresses": [
                 "8.8.8.8",
                 "8.8.4.4"
                ],
                "enabled": true
               }
              ```
              Note: The function wraps this single port in a list for the API call. If "name" is not provided in `mgmt_port`, it defaults to "eth0".

    Returns:
        dict: JSON response
    """
    fabricId = mgmt_port_data_obj["fabric_id"]
    nodeId = mgmt_port_data_obj["node_id"]
    if "name" not in mgmt_port_data_obj["mgmt_port"]:
        mgmt_port_data_obj["mgmt_port"]["name"] = "eth0"
    payload = {"ports": [mgmt_port_data_obj["mgmt_port"]]}
    response =_make_post_request(headers,
            f"{BASE_URL}/fabrics/{fabricId}/nodes/{nodeId}/managementPorts",payload=payload)
    return response

def update_management_port(mgmt_port_data_obj):
    """
    Updates the settings on a management port

    Args:
        mgmt_port_data_obj (dict): A dictionary containing fabric ID, node ID, and updated management port data. Expected keys:
            - "fabric_id" (str): The ID or name of the fabric.
            - "node_id" (str): The node id or name from which a device is bound.
            - "id" (str, optional): The ID of the port to update. If not provided, it uses `mgmt_port["name"]`.
            - "mgmt_port" (dict): A dictionary containing the updated properties for the management port. Must include "name" if "id" is not provided.

    Returns:
        dict: JSON response
    """
    fabricId = mgmt_port_data_obj["fabric_id"]
    nodeId = mgmt_port_data_obj["node_id"]
    if "id" in mgmt_port_data_obj:
      id = mgmt_port_data_obj["id"]
    else:
      id = mgmt_port_data_obj["mgmt_port"]["name"]
    payload = mgmt_port_data_obj["mgmt_port"]
    response = _make_put_request(headers, f"{BASE_URL}/fabrics/{fabricId}/nodes/{nodeId}/managementPorts/{id}", payload=payload)
    return response

def delete_management_port(mgmt_port_data_obj):
    """
    Updates management port with default values (cannot explicitly delete a management port).

    Args:
        mgmt_port_data_obj (dict): Data object containing necessary information to make the call. Expected keys:
            - "fabric_id" (str): The ID or name of the fabric.
            - "node_id" (str): The ID or name of the node.
            - "mgmt_port" (dict): A dictionary containing the name of the management port to "delete" (reset to default).
              Example: {"mgmt_port": {"name": "eth0"}}

    Returns:
        dict: JSON response
    """
    fabricId = mgmt_port_data_obj["fabric_id"]
    nodeId = mgmt_port_data_obj["node_id"]
    id = mgmt_port_data_obj["mgmt_port"]["name"]
    payload = {}
    response = _make_put_request(headers, f"{BASE_URL}/fabrics/{fabricId}/nodes/{nodeId}/managementPorts/{id}", payload=payload)
    return response


# ------------------------------ PORTS ------------------------------


# /fabrics/{fabricId}/nodes/{nodeId}/ports/{portId}
def get_port(port_data_obj):
    """
    Retrieves a specific port by its ID.

    Args:
        port_data_obj (dict): A dictionary containing fabric ID, node ID, port ID, and optional parameters. Expected keys:
            - "fabric_id" (str): The ID or name of the fabric.
            - "node_id" (str): The ID or name of the node.
            - "port" (dict): A dictionary containing the port's name and optional query parameters.
              Expected sub-keys:
                - "name" (str): The ID of the port.
                - "candidate" (str, optional): The candidate configuration name. Defaults to None.
                - "includeMetadata" (bool, optional): Include object metadata in the response. Defaults to False.

    Returns:
        dict: JSON response, or None on error.
    """
    params = {key: port_data_obj["port"][key] for key in ["candidate", "includeMetadata"] if key in port_data_obj["port"]}
    fabricId = port_data_obj["fabric_id"]
    nodeId = port_data_obj["node_id"]
    portId = port_data_obj["port"]["name"]
    response = _make_get_request(headers, f"{BASE_URL}/fabrics/{fabricId}/nodes/{nodeId}/ports/{portId}", params=params)
    return response

def update_port(port_data_obj):
    """
    Updates a specific port.

    Args:
        port_data_obj (dict): A dictionary containing fabric ID, node ID, and updated port properties. Expected keys:
            - "fabric_id" (str): The ID or name of the fabric.
            - "node_id" (str): The ID or name of the node.
            - "port" (dict): A dictionary containing the updated port properties. Must include "name" for port ID.
              Example:
              ```json
              {
                "name": "Ethernet1_1",
                "description": "Updated port description",
                "enabled": true
              }
              ```

    Returns:
        dict: JSON response, or None on error.
    """
    fabricId = port_data_obj["fabric_id"]
    nodeId = port_data_obj["node_id"]
    portId = port_data_obj["port"]["name"]
    payload = port_data_obj["port"]
    response = _make_put_request(headers, f"{BASE_URL}/fabrics/{fabricId}/nodes/{nodeId}/ports/{portId}", payload=payload)
    return response


# ------------------------------ CONNECTIONS ------------------------------


# /fabrics/{fabricId}/connections
def get_fabric_connections(connection_data_obj):
    """
    Retrieves a list of connections within a fabric.

    Args:
        connection_data_obj (dict): A dictionary containing the fabric ID and optional parameters. Expected keys:
            - "fabric_id" (str): The ID or name of the fabric.
            - "connection" (dict, optional): A dictionary containing query parameters.
              Expected sub-keys:
                - "candidate" (str, optional): The candidate configuration name. Defaults to None.

    Returns:
        dict: JSON response, or None on error.
    """
    params = {key: connection_data_obj["connection"][key] for key in ["candidate"] if "connection" in connection_data_obj and key in connection_data_obj["connection"]}
    fabricId = connection_data_obj["fabric_id"]
    response = _make_get_request(headers, f"{BASE_URL}/fabrics/{fabricId}/connections", params=params)
    return response

# /fabrics/{fabricId}/connections/{connectionId}
def get_fabric_connection(connection_data_obj):
    """
    Retrieves a specific connection by ID.

    Args:
        connection_data_obj (dict): A dictionary containing fabric ID, connection ID, and optional parameters. Expected keys:
            - "fabric_id" (str): The ID or name of the fabric.
            - "connection" (dict): A dictionary containing the connection ID and optional query parameters.
              Expected sub-keys:
                - "connection_id" (str): The ID of the connection.
                - "candidate" (str, optional): Candidate configuration name. Defaults to None.

    Returns:
        dict: JSON response, or None on error.
    """
    params = {key: connection_data_obj["connection"][key] for key in ["candidate"] if key in connection_data_obj["connection"]}
    fabricId = connection_data_obj["fabric_id"]
    connectionId = connection_data_obj["connection"]["connection_id"]
    response = _make_get_request(headers, f"{BASE_URL}/fabrics/{fabricId}/connections/{connectionId}", params=params)
    return response

def add_fabric_connections(connection_data_obj):
    """
    Adds one or more connections to a fabric.

    Args:
        connection_data_obj (dict): A dictionary containing fabric ID and connection data. Expected keys:
            - "fabric_id" (str): The ID or name of the fabric.
            - "connection" (dict): A dictionary representing a single connection object to add.
              Example:
              ```json
              {
                "local": {
                  "portName": "Ethernet1_19",
                  "nodeName": "node-leaf0"
                },
                "remote": {
                  "portName": "Ethernet1_19",
                  "nodeName": "node-spine0"
                }
              }
              ```
              Note: The function wraps this single connection in a list for the API call.

    Returns:
        dict: JSON response, or None on error.
    """
    payload = {"connections": [connection_data_obj["connection"]]}
    fabricId = connection_data_obj["fabric_id"]
    response = _make_post_request(headers, f"{BASE_URL}/fabrics/{fabricId}/connections", payload=payload)
    return response

def set_fabric_connections(fabricId, connections):
    """
    Replaces all connections in a fabric with a new set of connections.

    Args:
        fabricId (str): The ID or name of the fabric.
        connections (list): A list of connections to set.
            Example:
            ```json
            [
              {
                "local": {
                  "portName": "Ethernet1_19",
                  "nodeName": "node-leaf0"
                },
                "remote": {
                  "portName": "Ethernet1_19",
                  "nodeName": "node-spine0"
                }
              }
            ]
            ```
    Returns:
        dict: JSON response, or None on error.
    """
    payload = {"connections": connections}
    response = _make_put_request(headers, f"{BASE_URL}/fabrics/{fabricId}/connections", payload=payload)
    return response

def delete_fabric_connection(connection_data_obj):
    """
    Delete a specific connection.
    Args:
        connection_data_obj (dict): A dictionary containing fabric ID and connection ID. Expected keys:
            - "fabric_id" (str): The ID or name of the fabric.
            - "id" (str): The ID of the connection to delete.

    Returns:
        dict: JSON response
    """
    fabricId = connection_data_obj["fabric_id"]
    connectionId = connection_data_obj["id"]
    response = _make_delete_request(headers, f"{BASE_URL}/fabrics/{fabricId}/connections/{connectionId}")
    return response


# ------------------------------ VNIs ------------------------------


def add_fabric_vnis(vni_data_obj):
    """
    Adds one or more VNIs to a fabric.

    Args:
        vni_data_obj (dict): A dictionary containing fabric ID and VNI data. Expected keys:
            - "fabric_id" (str): The ID or name of the fabric.
            - "vni" (dict): A dictionary representing a single VNI object to add.
              Example:
              ```json
              {
                "name": "vni-example-1001",
                "description": "Example VNI",
                "vni": 1001,
                "vrfId": "1234-4567-7890-abcd",
                "svis": [
                    {
                        "enabled": true,
                        "ipv4Addresses": ["10.1.1.1/24"],
                        "ipv6Addresses": ["2001:db8::1/64"]
                    }
                ],
                "labels": ["VLAN1001"]
              }
              ```
              Note: The function wraps this single VNI in a list for the API call. "enabled" is forced to True.

    Returns:
        dict: JSON response, or None on error.
    """
    payload = {"vnis": [vni_data_obj["vni"]]}
    fabricId = vni_data_obj["fabric_id"]
    vni_data_obj["vni"]["enabled"] = True  # Enabled MUST be true
    response = _make_post_request(headers, f"{BASE_URL}/fabrics/{fabricId}/vnis", payload=payload)
    return response

# /fabrics/{fabricId}/vnis/{vniId}
def get_fabric_vni(vni_data_obj):
    """
    Retrieves a specific VNI by ID or name.

    Args:
        vni_data_obj (dict): A dictionary containing fabric ID, VNI ID, and optional parameters. Expected keys:
            - "fabric_id" (str): The ID or name of the fabric.
            - "vni" (dict): A dictionary containing the VNI's name and optional query parameters.
              Expected sub-keys:
                - "name" (str): The ID or name of the VNI.
                - "candidate" (str, optional): The candidate configuration name. Defaults to None.
                - "includeMetadata" (bool, optional): Include object Metadata in the response. Defaults to False.

    Returns:
        dict: JSON response, or None on error.
    """
    params = {key: vni_data_obj["vni"][key] for key in ["candidate", "includeMetadata"] if key in vni_data_obj["vni"]}
    fabricId = vni_data_obj["fabric_id"]
    vniId = vni_data_obj["vni"]["name"]
    response = _make_get_request(headers, f"{BASE_URL}/fabrics/{fabricId}/vnis/{vniId}", params=params)
    return response

def update_fabric_vni(vni_data_obj):
    """
    Updates a specific VNI.

    Args:
        vni_data_obj (dict): A dictionary containing fabric ID, VNI ID, and updated VNI properties. Expected keys:
            - "fabric_id" (str): The ID or name of the fabric.
            - "vni" (dict): A dictionary containing the updated VNI properties. Must include "name" for VNI ID.
              Example:
              ```json
              {
                "name": "vni-example-1001",
                "description": "Updated VNI description",
                "enabled": true
              }
              ```
              Note: "enabled" is forced to True.

    Returns:
        dict: JSON response, or None on error.
    """
    fabricId = vni_data_obj["fabric_id"]
    vniId = vni_data_obj["vni"]["name"]
    payload = vni_data_obj["vni"]
    vni_data_obj["vni"]["enabled"] = True  # Enabled MUST be true
    response = _make_put_request(headers, f"{BASE_URL}/fabrics/{fabricId}/vnis/{vniId}", payload=payload)
    return response

def delete_fabric_vni(vni_data_obj):
   """
    Deletes a VNI given its ID

    Args:
        vni_data_obj (dict): A dictionary containing fabric ID and VNI ID. Expected keys:
            - "fabric_id" (str): The ID or name of the fabric.
            - "id" (str): The ID or name of the VNI to delete.

    Returns:
        dict: JSON response
   """
   fabricId = vni_data_obj["fabric_id"]
   vniId = vni_data_obj["id"]
   response = _make_delete_request(headers, f"{BASE_URL}/fabrics/{fabricId}/vnis/{vniId}")
   return response


# ------------------------------ VRFs ------------------------------


def add_fabric_vrfs(vrf_data_obj):
    """
    Creates or updates one or more VRFs with a specific name.

    Args:
        vrf_data_obj (dict): A dictionary containing fabric ID and VRF data. Expected keys:
            - "fabric_id" (str): The ID or name of the fabric.
            - "vrf" (dict): A dictionary representing a single VRF object to add.
              Example:
              ```json
              {
               "name": "Vrf-exampleOne",
               "enabled": true
              }
              ```
              Note: The function wraps this single VRF in a list for the API call. "enabled" is forced to True.

    Returns:
        dict: JSON response, or None on error.
    """
    payload = {"vrfs": [vrf_data_obj["vrf"]]}
    fabricId = vrf_data_obj["fabric_id"]
    vrf_data_obj["vrf"]["enabled"] = True  # Enabled MUST be true
    response = _make_post_request(headers,f"{BASE_URL}/fabrics/{fabricId}/vrfs", payload=payload)
    return response

# /fabrics/{fabricId}/vrfs/{vrfId}
def get_fabric_vrf(vrf_data_obj):
    """
    Gets details for a VRF.

    Args:
        vrf_data_obj (dict): A dictionary containing fabric ID, VRF ID, and optional parameters. Expected keys:
            - "fabric_id" (str): The ID or name of the fabric.
            - "vrf" (dict): A dictionary containing the VRF's name and optional query parameters.
              Expected sub-keys:
                - "name" (str): The ID or name of the VRF.
                - "candidate" (str, optional): The candidate configuration name. Defaults to None.
                - "includeMetadata" (bool, optional): Include object metadata in the response. Defaults to False.

    Returns:
        dict: JSON response, or None on error.
    """
    params = {key: vrf_data_obj["vrf"][key] for key in ["candidate", "includeMetadata"] if key in vrf_data_obj["vrf"]}
    fabricId = vrf_data_obj["fabric_id"]
    vrfId = vrf_data_obj["vrf"]["name"]
    response = _make_get_request(headers, f"{BASE_URL}/fabrics/{fabricId}/vrfs/{vrfId}", params=params)
    return response

def update_fabric_vrf(vrf_data_obj):
    """
    Updates a specific VRF.
    Note: This function currently only performs a GET request for the VRF due to API limitations.
    The PUT API call for VRF updates is not currently supported/working as intended.

    Args:
        vrf_data_obj (dict): A dictionary containing fabric ID, VRF ID, and updated VRF properties. Expected keys:
            - "fabric_id" (str): The ID or name of the fabric.
            - "vrf" (dict): A dictionary containing the VRF's name and updated properties.
              Example:
              ```json
              {
              "name": "Vrf-examplevrf1",
              "annotations": [
                {
                "name": "position",
                "value": "1234"
                }
              ],
              "enabled": true,
              "isDefault": true
              }
              ```
              Note: "enabled" is forced to True in the commented-out PUT logic.

    Returns:
        dict: JSON response from the GET request, or None on error.
    """
    return get_fabric_vrf(vrf_data_obj) # Needs to return a response with 200 status code, and you (should) only get here if the GET was successful

    # PUT API CALL NOT CURRENTLY SUPPORTED/WORKING, but here's the code anyways :)
    fabricId = vrf_data_obj["fabric_id"]
    vrfId = vrf_data_obj["vrf"]["name"]
    payload = vrf_data_obj["vrf"]
    vrf_data_obj["vrf"]["enabled"] = True  # Enabled MUST be true
    response = _make_put_request(headers, f"{BASE_URL}/fabrics/{fabricId}/vrfs/{vrfId}", payload=payload)
    return response

def delete_fabric_vrf(vrf_data_obj):
    """
      Deletes a specific VRF object.
      Args:
        vrf_data_obj (dict): A dictionary containing fabric ID and VRF ID. Expected keys:
          - "fabric_id" (str): The ID or name of the fabric.
          - "vrf" (dict): A dictionary containing the VRF's name.
            Example: {"vrf": {"name": "Vrf-to-delete"}}
      Returns:
        dict: JSON response
    """
    fabricId = vrf_data_obj["fabric_id"]
    vrfId = vrf_data_obj["vrf"]["name"]
    response = _make_delete_request(headers, f"{BASE_URL}/fabrics/{fabricId}/vrfs/{vrfId}")
    return response


# ------------------------------ STATIC ROUTES ------------------------------


def add_fabric_static_routes(static_route_data_obj):
    """
    Creates or updates one or more static routes for a fabric VRF object.

    Args:
        static_route_data_obj (dict): A dictionary containing fabric ID, VRF ID, and static route data. Expected keys:
            - "fabric_id" (str): The ID or name of the fabric.
            - "vrf_id" (str): The ID or name of the VRF.
            - "static_route" (dict): A dictionary representing a single static route object to add.
              Example payload for "static_route":
              ```json
              {
                "name": "Vrf-exampleOne-SR1",
                "enabled": true,
                "routes": [
                  {
                    "prefix": "10.10.10.0/24",
                    "preference": 10,
                    "discard": true
                  }
                ]
              }
              ```
              Note: The function wraps this single static route in a list for the API call.

    Returns:
        dict: JSON response, or None on error.
    """
    payload = {"staticRoutes": [static_route_data_obj["static_route"]]}
    fabricId = static_route_data_obj["fabric_id"]
    vrfId = static_route_data_obj["vrf_id"]
    response = _make_post_request(headers,f"{BASE_URL}/fabrics/{fabricId}/vrfs/{vrfId}/staticRoutes",payload=payload)
    return response

# /fabrics/{fabricId}/vrfs/{vrfId}/staticRoutes/{routeId}
def get_fabric_static_route(static_route_data_obj):
    """
     Gets information for a single fabric static Route.

     Args:
         static_route_data_obj (dict): A dictionary containing fabric ID, VRF ID, static route ID, and optional parameters. Expected keys:
             - "fabric_id" (str): The ID or name of the fabric.
             - "vrf_id" (str): The ID or name of the VRF.
             - "static_route" (dict): A dictionary containing the static route's name and optional query parameters.
               Expected sub-keys:
                 - "name" (str): The ID or name of the static route.
                 - "candidate" (str, optional): The candidate configuration name. Defaults to None.
                 - "includeMetadata" (bool, optional): Include object metadata in the response. Defaults to False.

    Returns:
        int: JSON response on success or None on Fail
    """
    params = {key: static_route_data_obj["static_route"][key] for key in ["candidate", "includeMetadata"] if key in static_route_data_obj["static_route"]}
    fabricId = static_route_data_obj["fabric_id"]
    vrfId = static_route_data_obj["vrf_id"]
    routeId = static_route_data_obj["static_route"]["name"]
    response = _make_get_request(headers, f"{BASE_URL}/fabrics/{fabricId}/vrfs/{vrfId}/staticRoutes/{routeId}", params=params)
    return response

def update_fabric_static_route(static_route_data_obj):
    """
     Updates a specific static route for a given VRF object.

     Args:
         static_route_data_obj (dict): A dictionary containing fabric ID, VRF ID, static route ID, and updated static route properties. Expected keys:
             - "fabric_id" (str): The ID or name of the fabric.
             - "vrf_id" (str): The ID or name of the VRF.
             - "static_route" (dict): A dictionary containing the updated static route properties. Must include "name" for route ID.
               Example:
               ```json
               {
                 "name": "Vrf-exampleOne-SR1",
                 "enabled": true,
                 "routes": [
                   {
                     "prefix": "10.10.10.0/24",
                     "preference": 20,
                     "discard": false
                   }
                 ]
               }
               ```
      Returns:
        dict: JSON response from the GET request, or None on error.
    """
    fabricId = static_route_data_obj["fabric_id"]
    vrfId = static_route_data_obj["vrf_id"]
    routeId = static_route_data_obj["static_route"]["name"]
    payload = static_route_data_obj["static_route"]
    response = _make_put_request(headers, f"{BASE_URL}/fabrics/{fabricId}/vrfs/{vrfId}/staticRoutes/{routeId}", payload=payload)
    return response

def delete_fabric_static_route(static_route_data_obj):
   """
    Deletes a static route for a VRF ID in a fabric.

    Args:
         static_route_data_obj (dict): A dictionary containing fabric ID, VRF ID, and static route ID. Expected keys:
             - "fabric_id" (str): The ID or name of the fabric.
             - "vrf_id" (str): The ID or name of the VRF.
             - "static_route" (dict): A dictionary containing the name of the static route to delete.
               Example: {"static_route": {"name": "Vrf-exampleOne-SR1"}}
    Returns:
        dict: JSON response
   """
   fabricId = static_route_data_obj["fabric_id"]
   vrfId = static_route_data_obj["vrf_id"]
   routeId = static_route_data_obj["static_route"]["name"]
   response = _make_delete_request(headers, f"{BASE_URL}/fabrics/{fabricId}/vrfs/{vrfId}/staticRoutes/{routeId}")
   return response


# ------------------------------ GET FABRIC CONFIG ------------------------------


def get_fabric_configurations(fabric_data):
    """
    Retrieves the configuration for a specific fabric.

    Args:
        fabric_data (dict): A dictionary containing the fabric ID and optional parameters. Expected keys:
            - "name" (str): The ID or name of the fabric.
            - "candidate" (str, optional): The candidate configuration name. Defaults to None.
            - "includeMetadata" (bool, optional): Include object metadata in the response. Defaults to False.

    Returns:
        dict: JSON response containing the fabric configuration, or None on error.
    """
    params = {key: fabric_data[key] for key in ["candidate", "includeMetadata"] if key in fabric_data}
    fabricId = fabric_data["name"]
    response = _make_get_request(headers, f"{BASE_URL}/fabrics/{fabricId}/configurations", params=params)
    return response


# ------------------------------ BINDING ------------------------------


# /devices
def get_devices():
    """
    Retrieves a list of devices.

    Returns:
        dict: JSON response containing the list of devices, or None on error.
    """
    response = _make_get_request(headers, f"{BASE_URL}/devices")
    return response

# /fabrics/{fabricId}/nodes/{nodeId}/devices/{deviceId}
def bind_device(bind_data_obj):
    """
    Binds a device to a specific node.
     Args:
        bind_data_obj (dict): A dictionary containing fabric ID, node ID, and device ID. Expected keys:
            - "fabric_id" (str): The ID or name of the fabric.
            - "node_id" (str): The ID or name of the node.
            - "device_id" (str): The serial of the device.

    Returns:
         dict: JSON response or None on Error
    """
    fabricId = bind_data_obj["fabric_id"]
    nodeId = bind_data_obj["node_id"]
    deviceId = bind_data_obj["device_id"]
    response = _make_put_request(headers, f"{BASE_URL}/fabrics/{fabricId}/nodes/{nodeId}/devices/{deviceId}")
    return response

# /fabrics/{fabricId}/nodes/{nodeId}/devices
def unbind_device(auth, fabricId, nodeId):
    """
    Unbinds a device from a specific node
     Args:
        fabricId (str): The ID or name of the fabric.
        nodeId (str): The ID or name of the node.

    Returns:
         Int: Response Code or None on Error
    """
    response = _make_delete_request(auth, f"{BASE_URL}/fabrics/{fabricId}/nodes/{nodeId}/devices")
    return response


# ------------------------------ FROM HYPERFABRIC_SDK ------------------------------


# /bearerTokens
def get_bearer_tokens(auth, include_metadata=False):
    """
    Retrieves a list of bearer tokens.
    Args:
        include_metadata (bool, optional): Include metadata in the response. Defaults to False.
    Returns:
        dict: JSON response containing the list of bearer tokens, or None on error.
    """
    params = {"includeMetadata": include_metadata}
    response = _make_get_request(auth, f"{BASE_URL}/bearerTokens", params=params)
    return response

def create_bearer_token(auth, name, description, scope, notBefore, notAfter):
    """
    Creates a new bearer token.
    Args:
        name (str): The user provided name for the token.
        description (str): A description for the token.
        scope (str):  The permission scope of the token.
        notBefore (str): Sets the time at which the token can be used.
        notAfter (str): Sets the time after which the token cannot be used.
    Returns:
         dict: JSON response of the new created token or None on error
    """
    payload = {
        "tokens": [
            {
                "name": name,
                "description": description,
                "scope": scope,
                "notBefore": notBefore,
                "notAfter": notAfter
            }
        ]
    }
    response =_make_post_request(auth,f"{BASE_URL}/bearerTokens",payload=payload)
    response.raise_for_status()
    return response.json()

# /bearerTokens/{tokenId}
def get_bearer_token(auth, tokenId, include_metadata=False):
    """
    Retrieves a specific bearer token by its ID.
    Args:
        tokenId (str): The ID of the bearer token.
        include_metadata (bool, optional): Include metadata in the response. Defaults to False.
    Returns:
        dict: JSON response containing the bearer token, or None on error.
    """
    params = {"includeMetadata": includeMetadata}
    response = _make_get_request(auth, f"{BASE_URL}/bearerTokens/{tokenId}", params=params)
    return response

def delete_bearer_token(auth, tokenId):
    """
    Deletes a specific bearer token by its ID.
    Args:
        tokenId (str): The ID of the bearer token to delete.
    Returns:
        int: HTTP status code, or None on error.
    """
    response = _make_delete_request(auth, f"{BASE_URL}/bearerTokens/{tokenId}")
    return response

# /devices
# def get_devices(auth):
#     """
#     Retrieves a list of devices.

#     Returns:
#         dict: JSON response containing the list of devices, or None on error.
#     """
#     response = _make_get_request(auth, f"{BASE_URL}/devices")
#     return response

# /fabrics/{fabricId}/candidates
def get_fabric_candidates(auth, fabricId, name=None, txnId=None, needInactive=None, needReviews=None, needEvents=None, startTime=None, endTime=None):
    """
    Retrieves a list of candidate configurations for a specific fabric.
    Args:
        fabricId (str): The ID or name of the fabric.
        name (str, optional): The candidate configuration name. Defaults to None.
        txnId (int, optional): The transaction sequence number. Defaults to None.
        needInactive (bool, optional): Include committed/reverted candidate configurations. Defaults to None.
        needReviews (bool, optional): Include the list of reviews. Defaults to None.
        needEvents (bool, optional): Include the list of activity events. Defaults to None.
        startTime (str, optional): Start value of time range. Defaults to None.
        endTime (str, optional): End value of the time range. Defaults to None.
    Returns:
        dict: JSON response containing the list of candidate configurations, or None on error.
    """
    params = {}
    if name:
        params["name"] = name
    if txnId:
        params["txnId"] = txnId
    if needInactive:
        params["needInactive"] = needInactive
    if needReviews:
        params["needReviews"] = needReviews
    if needEvents:
        params["needEvents"] = needEvents
    if startTime:
        params["startTime"] = startTime
    if endTime:
        params["endTime"] = endTime
    response = _make_get_request(auth, f"{BASE_URL}/fabrics/{fabricId}/candidates", params=params)
    return response

# /fabrics/{fabricId}/candidates/{name}
def get_fabric_candidate(auth, fabricId, name, needInactive=None, needReviews=None, needEvents=None):
    """
    Retrieves a specific candidate configuration for a fabric.

    Args:
        fabricId (str): The ID or name of the fabric.
        name (str): The name of the candidate configuration.
        needInactive (bool, optional): Include committed/reverted candidate configuration.  Defaults to None.
        needReviews (bool, optional): Include the list of reviews. Defaults to None.
        needEvents (bool, optional): Include the list of activity events. Defaults to None.

    Returns:
        dict: JSON response containing the candidate configuration, or None on error.
    """
    params = {}
    if needInactive:
        params["needInactive"] = needInactive
    if needReviews:
        params["needReviews"] = needReviews
    if needEvents:
        params["needEvents"] = needEvents

    response = _make_get_request(auth, f"{BASE_URL}/fabrics/{fabricId}/candidates/{name}", params=params)
    return response

def review_fabric_candidate(auth, fabricId, name, comments):
    """
    Adds a comment (review) to a specific candidate configuration.

    Args:
        fabricId (str): The ID or name of the fabric.
        name (str): The name of the candidate configuration.
        comments (str): The review comments to add.

    Returns:
        dict: JSON response, or None on error.
    """
    payload = {"comments": comments}
    response = _make_put_request(auth, f"{BASE_URL}/fabrics/{fabricId}/candidates/{name}", payload=payload)
    return response

def commit_fabric_candidate(auth, fabric_name, name, comments):
    """
    Commits a specific candidate configuration to the running configuration of a fabric.

    Args:
        fabricId (str): The ID or name of the fabric.
        name (str): The name of the candidate configuration.
        comments (str): The commit comments.

    Returns:
        dict: JSON response, or None on error.
    """
    payload = {"comments": comments}
    url = f"{BASE_URL}/fabrics/{fabric_name}/candidates/{name}"
    response = _make_post_request(auth, url, payload=payload)
    return response

def revert_fabric_candidate(auth, fabricId, name):
    """
    Discards (reverts) a specific candidate configuration.

    Args:
        fabricId (str): The ID or name of the fabric.
        name (str): The name of the candidate configuration.

    Returns:
        int: HTTP status code, or None on error.
    """
    response = _make_delete_request(auth, f"{BASE_URL}/fabrics/{fabricId}/candidates/{name}")
    return response

def delete_fabric_connections(auth, fabricId):
    """
    Deletes all connections in the fabric.
    Args:
        fabricId (str): The ID or name of the fabric.
    """
    response = _make_delete_request(auth, f"{BASE_URL}/fabrics/{fabricId}/connections")
    return response

# /fabrics/{fabricId}/nodes/{nodeId}/ports
def get_ports(auth, fabricId, nodeId, candidate=None, includeMetadata=None):
    """
    Retrieves a list of ports for a specific node.

    Args:
        fabricId (str): The ID or name of the fabric.
        nodeId (str): The ID or name of the node.
        candidate (str, optional): The candidate configuration name. Defaults to None.
        includeMetadata (bool, optional): Include object metadata in the response. Defaults to False.

    Returns:
        dict: JSON response, or None on error.
    """
    params = {}
    if candidate:
        params["candidate"] = candidate
    if includeMetadata:
        params["includeMetadata"] = includeMetadata
    response = _make_get_request(auth, f"{BASE_URL}/fabrics/{fabricId}/nodes/{nodeId}/ports", params=params)
    return response

def set_ports(auth, fabricId, nodeId, ports):
    """
    Replaces all ports for a specific node.

    Args:
        fabricId (str): The ID or name of the fabric.
        nodeId (str): The ID or name of the node.
        ports (list): A list of port objects to set.

        Here is an example:
        ```json
         [
          {
           "name": "Ethernet1_5",
           "enabled": true,
           "roles": [
            "HOST_PORT"
           ]
          },
          {
           "name": "Ethernet1_6",
           "enabled": true,
           "roles": [
            "HOST_PORT"
           ]
          },
          {
           "name": "Ethernet1_7",
           "enabled": true,
           "roles": [
            "HOST_PORT"
           ]
          },
          {
           "name": "Ethernet1_8",
           "enabled": true,
           "roles": [
            "HOST_PORT"
           ]
          }
         ]
        ```

    Returns:
        dict: JSON response, or None on error.
    """
    payload = {"ports": ports}
    response = _make_put_request(auth, f"{BASE_URL}/fabrics/{fabricId}/nodes/{nodeId}/ports", payload=payload)
    return response

# /fabrics/{fabricId}/vnis
def get_fabric_vnis(auth, fabricId, candidate=None, includeMetadata=None):
    """
    Retrieves a list of VNIs within a fabric.

    Args:
        fabricId (str): The ID or name of the fabric.
        candidate (str, optional): The candidate configuration name. Defaults to None.
        includeMetadata (bool, optional): Include object metadata in the response. Defaults to False.

    Returns:
        dict: JSON response, or None on error.
    """
    params = {}
    if candidate:
        params["candidate"] = candidate
    if includeMetadata:
        params["includeMetadata"] = includeMetadata
    response = _make_get_request(auth, f"{BASE_URL}/fabrics/{fabricId}/vnis", params=params)
    return response

# /fabrics/{fabricId}/vnis/{vniId}/members
def get_fabric_vni_members(auth, fabricId, vniId, candidate=None, includeMetadata=None):
    """
    Retrieves a list of vni members from a fabric.

    Args:
        fabricId (str): The ID or name of the fabric.
        vniId (str): The ID or name of the vni.
        candidate (str, optional): The candidate configuration name. Defaults to None.
        includeMetadata (bool, optional): Include object metadata in the response. Defaults to False.

    Returns:
        dict: JSON response, or None on error.
    """
    params = {}
    if candidate:
        params["candidate"] = candidate
    if includeMetadata:
        params["includeMetadata"] = includeMetadata
    response = _make_get_request(auth, f"{BASE_URL}/fabrics/{fabricId}/vnis/{vniId}/members", params=params)
    return response

def add_fabric_vni_members(auth, fabricId, vniId, payload):
    """
        Adds one or more vni member to a fabric vni object

        Args:
            fabricId (str): The ID or name of the fabric.
            vrfId (str): A list of user-defined labels that can be used for grouping and filtering VRFs.
            payload (str, optional): The Route Tag Defaults to None
    """
    payload = {"members": payload}
    response = _make_post_request(auth,
            f"{BASE_URL}/fabrics/{fabricId}/vnis/{vniId}/members", payload=payload)
    return response

# /fabrics/{fabricId}/vnis/{vniId}/members/{memberId}
def get_fabric_vni_member(auth, fabricId, vniId, memberId, candidate=None, includeMetadata=None):
    """
     Gets details for a vni member
     Args:
        fabricId (str): The ID or name of the fabric.
        vniId (str): A list of user-defined labels that can be used for grouping and filtering VRFs.
        memberId (str, optional): The name for the device you are listing information for. Defaults to None

    Returns:
        int: JSON response on success or None on Fail
    """
    params = {}
    if candidate:
        params["candidate"] = candidate
    if includeMetadata:
        params["includeMetadata"] = includeMetadata
    response = _make_get_request(auth, f"{BASE_URL}/fabrics/{fabricId}/vnis/{vniId}/members/{memberId}", params=params)
    return response

def delete_fabric_vni_member(auth, fabricId, vniId, memberId):
    """
     Deletes a VNI member given its ID.

      Args:
          fabricId (str): The ID or name of the fabric.
          vniId (str): A list of user-defined labels that can be used for grouping and filtering VRFs.
          memberId (str, optional): The name for the device you are listing deleting a VNI device
    """
    response = _make_delete_request(auth, f"{BASE_URL}/fabrics/{fabricId}/vnis/{vniId}/members/{memberId}")
    return response

# /fabrics/{fabricId}/vrfs
def get_fabric_vrfs(auth, fabricId, candidate=None, includeMetadata=None):
    """
    Retrieves a list of VRFs within a fabric.

    Args:
        fabricId (str): The ID or name of the fabric.
        candidate (str, optional): The candidate configuration name. Defaults to None.
        includeMetadata (bool, optional): Include object metadata in the response. Defaults to False.

    Returns:
        dict: JSON response, or None on error.
    """
    params = {}
    if candidate:
        params["candidate"] = candidate
    if includeMetadata:
        params["includeMetadata"] = includeMetadata
    response = _make_get_request(auth, f"{BASE_URL}/fabrics/{fabricId}/vrfs", params=params)
    return response

# /fabrics/{fabricId}/vrfs/{vrfId}/staticRoutes
def get_fabric_static_routes(auth, fabricId, vrfId, candidate=None, includeMetadata=None):
    """
     Gets a list of staticRoutes for a vrf

     Args:
         fabricId (str): The ID or name of the fabric.
         vrfId (str): The unique identifier of the VRF to which this static routes belong to.
         candidate (str, optional): The candidate configuration name. Defaults to None.
         includeMetadata (bool, optional): Include object metadata in the response. Defaults to False.

    Returns:
        dict: JSON response, or None on error.
    """
    params = {}
    if candidate:
        params["candidate"] = candidate
    if includeMetadata:
        params["includeMetadata"] = includeMetadata
    response = _make_get_request(auth, f"{BASE_URL}/fabrics/{fabricId}/vrfs/{vrfId}/staticRoutes", params=params)
    return response

# /users
def get_users(auth, emails=None, enabled=None, roles=None, includeMetadata=None):
    """
    Retrieves a list of users.

    Args:
        emails (str, optional): Filter by one or more email addresses. Defaults to None.
        enabled (bool, optional): Only return users that are administratively enabled. Defaults to None.
        roles (str, optional): Only return users with specific roles (ADMIN, READ_WRITE, READ_ONLY). Defaults to None.
        includeMetadata (bool, optional): Include object metadata in the response. Defaults to False.

    Returns:
        dict: JSON response, or None on error.
    """
    params = {}
    if emails:
        params["emails"] = emails
    if enabled:
        params["enabled"] = enabled
    if roles:
        params["roles"] = roles
    if includeMetadata:
        params["includeMetadata"] = includeMetadata
    response = _make_get_request(auth, f"{BASE_URL}/users", params=params)
    return response

def add_users(auth, users):
    """
    Adds one or more users to the organization.
    Args:
        users (list): A list of user objects to add.

    Returns:
        dict: JSON response, or None on error.
    """
    payload = {"users": users}
    response = _make_post_request(auth, f"{BASE_URL}/users",payload=payload)
    return response

# /users/{id}
def get_user(auth, id, includeMetadata=None):
    """
    Retrieves a specific user by ID or email.
    Args:
        id (str): The ID or email of the user.
        includeMetadata (bool, optional): Include object metadata in the response. Defaults to False.

    Returns:
        dict: JSON response containing the user information, or None on error.
    """
    params = {}
    if includeMetadata:
        params["includeMetadata"] = includeMetadata
    response = _make_get_request(auth, f"{BASE_URL}/users/{id}", params=params)
    return response

def update_user(auth, id, payload):
    """
    Updates a specific user.

    Args:
        id (str): The ID or email of the user.
        payload (dict): A JSON payload containing the updated user properties.
        Example Payload:
        ```json
        {
         "enabled": true,
         "labels": ["LAB_ONE", "LAB_TWO"],
         "role": "READ_ONLY"
        }
        ```

    Returns:
        dict: JSON response, or None on error.
    """
    response = _make_put_request(auth, f"{BASE_URL}/users/{id}", payload=payload)
    return response

def delete_user(auth, id):
    """
    Deletes a specific user.

    Args:
        id (str): The ID or email of the user.

    Returns:
        int: HTTP status code, or None on error.
    """
    response = _make_delete_request(auth, f"{BASE_URL}/users/{id}")
    return response