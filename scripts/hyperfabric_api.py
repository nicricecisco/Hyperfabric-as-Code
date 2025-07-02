import requests, json, os
from pprint import pprint
from schemas.fabric_schema import validate_fabric

BASE_URL = "https://hyperfabric.cisco.com/api/v1"
TOKEN = os.environ['HYPERFABRIC_TOKEN']

headers = {
  "Content-Type": "application/json",
  "Accept": "application/json",
  "Authorization": f"Bearer {TOKEN}",
}

def _make_get_request(headers, url, params=None):
    return requests.get(url, headers=headers, params=params)

# def _make_get_request(headers, url, params=None):
#     try:
#         response = requests.get(url, headers=headers, params=params)
#         response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

#         try:
#             return response.json()
#         except json.JSONDecodeError:
#             print(f"JSON Decode Error: Response could not be decoded into JSON.  Raw response text: {response.text}")
#             return response.text # Return raw text if JSON decoding fails

#     except requests.exceptions.HTTPError as e:
#         try:
#             error_message = response.json()
#         except json.JSONDecodeError:
#             error_message = response.text

#         print(f"HTTP Error making GET request to {url}: {e}.  Status code: {response.status_code}.  Response content: {error_message}")
#         return None
#     except requests.exceptions.RequestException as e:
#         print(f"Request failed for GET to {url}: {e}")
#         return None
#     except Exception as e:
#         print(f"An unexpected error occurred during GET request to {url}: {e}")
#         return None


def _make_delete_request(headers, url):
    try:
        response = requests.delete(url, headers=headers)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

        try:
            return response.json()
        except json.JSONDecodeError:
            return response.status_code  # success, but text instead of json.

    except requests.exceptions.HTTPError as e:
        try:
            error_message = response.json()
        except json.JSONDecodeError:
            error_message = response.text

        print(f"HTTP Error making DELETE request to {url}: {e}.  Status code: {response.status_code}.  Response content: {error_message}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Request failed for DELETE to {url}: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during DELETE request to {url}: {e}")
        return None

def _make_put_request(headers, url, payload=None):
    return requests.put(url, headers=headers, json=payload)

# def _make_put_request(headers, url, payload=None):
#     try:
#         response = requests.put(url, headers=headers, json=payload)
#         response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

#         try:
#             return response.json()
#         except json.JSONDecodeError:
#             print(f"JSON Decode Error: Response could not be decoded into JSON.  Raw response text: {response.text}")
#             return response.text # if cannot decode json return the raw response

#     except requests.exceptions.HTTPError as e:
#         try:
#             error_message = response.json()
#         except json.JSONDecodeError:
#             error_message = response.text

#         print(f"HTTP Error making PUT request to {url}: {e}.  Status code: {response.status_code}.  Response content: {error_message}")
#         return None
#     except requests.exceptions.RequestException as e:
#         print(f"Request failed for PUT to {url}: {e}")
#         return None
#     except Exception as e:
#         print(f"An unexpected error occurred during PUT request to {url}: {e}")
#         return None
    
def _make_post_request(headers, url, payload=None):
    return requests.post(url, headers=headers, json=payload)
    
# def _make_post_request(headers, url, payload=None):
#     try:
#         response = requests.post(url, headers=headers, json=payload)
#         response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
#         try:
#             return response.json() # try to decode response to json
#         except json.JSONDecodeError:
#             print(f"JSON Decode Error: Response could not be decoded into JSON.  Raw response text: {response.text}")
#             return response.text # if cannot decode json return the raw response.

#     except requests.exceptions.HTTPError as e:
#         try:
#             error_message = response.json()  # Attempt to get the error message from the JSON response
#         except json.JSONDecodeError:
#             error_message = response.text  # If JSON decoding fails, get the raw response text

#         print(f"HTTP Error making POST request to {url}: {e}.  Status code: {response.status_code}.  Response content: {error_message}")
#         return None # Return None on error
#     except requests.exceptions.RequestException as e:
#         print(f"Request failed for POST to {url}: {e}")
#         return None  # Return None on error
#     except Exception as e:
#         print(f"An unexpected error occurred during POST request to {url}: {e}")
#         return None

# /fabrics
def get_fabrics():
    url = f"{BASE_URL}/fabrics"
    response = _make_get_request(headers, url)

    return response

def create_fabric(fabric_data):
    """
    Creates a new fabric.
    Args:
        fabric_name (str): The name of the fabric.  Must be unique and DNS compliant.
        description (str): A description of the fabric.
        location (str): A location identifier.
        address (str): The street address.
        city (str): The city.
        country (str): The two-letter country code.
        labels (list, optional): A list of labels for the fabric. Defaults to [].
        topology (str, optional): The fabric topology (MESH or SPINE_LEAF). Defaults to None.

    Returns:
        dict: JSON response containing the created fabric information, or None on error.
    """

    url = f"{BASE_URL}/fabrics"
    response = _make_post_request(headers, url, payload=fabric_data)

    return response

# /fabrics/{fabricId}
def get_fabric(fabric_data):
    """
    Retrieves a specific fabric.
    Args:
        fabricId (str): The ID or name of the fabric.
        candidate (str, optional): The candidate configuration name. Defaults to None.
        include_metadata (bool, optional): Include object metadata in the response. Defaults to False.
    Returns:
        dict: JSON response containing the fabric information, or None on error.
    """
    fabricId = fabric_data["fabrics"][0]["name"]
    response = _make_get_request(headers, f"{BASE_URL}/fabrics/{fabricId}")
    
    # response = requests.get(f"{BASE_URL}/fabrics/{fabricId}", headers=headers)
    return response

def update_fabric(fabric_data):
    """
    Updates a specific fabric.

    Args:
        fabricId (str): The ID or name of the fabric.
        payload (dict): A JSON payload containing the updated fabric properties. The keys depend upon #/components/schemas/configFabric:
          * name (str, optional):  The user-defined name of the fabric
          * description (str, optional): The description of the fabric.
          * location (str, optional): The location of the fabric.
          * address (str, optional): The street address.
          * city (str, optional): The city.
          * country (str, optional): The two-letter country code.
          * labels (list, optional): A list of labels for the fabric.

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
    fabricId = fabric_data["fabrics"][0]["name"]
    response = _make_put_request(headers, f"{BASE_URL}/fabrics/{fabricId}", payload=fabric_data["fabrics"][0])
    return response

def delete_fabric(auth, fabricId):
    """
    Deletes a specific fabric.
    Args:
        fabricId (str): The ID or name of the fabric to delete.
    Returns:
        int: HTTP status code, or None on error.
    """
    response = _make_delete_request(auth, f"{BASE_URL}/fabrics/{fabricId}")
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
def get_devices(auth):
    """
    Retrieves a list of devices.

    Returns:
        dict: JSON response containing the list of devices, or None on error.
    """
    response = _make_get_request(auth, f"{BASE_URL}/devices")
    return response

# /fabrics
# def get_fabrics(auth, fabricId=None, candidate=None, include_metadata=False):
#     """
#     Retrieves a list of fabrics.
#     Args:
#         fabricId (str, optional): Filter by one or more fabric ids and or names. Defaults to None.
#         candidate (str, optional): The candidate configuration name. Defaults to None.
#         include_metadata (bool, optional): Include object metadata in the response. Defaults to False.
#     Returns:
#         dict: JSON response containing the list of fabrics, or None on error.
#     """
#     params = {}
#     if fabricId:
#         params["fabricId"] = fabricId
#     if candidate:
#         params["candidate"] = candidate
#     if include_metadata:
#         params["includeMetadata"] = includeMetadata

#     response = _make_get_request(auth, f"{BASE_URL}/fabrics", params=params)
#     return response

# def create_fabric(auth, fabric_name, description, location, address, city, country, labels, topology=None):
#     """
#     Creates a new fabric.
#     Args:
#         fabric_name (str): The name of the fabric.  Must be unique and DNS compliant.
#         description (str): A description of the fabric.
#         location (str): A location identifier.
#         address (str): The street address.
#         city (str): The city.
#         country (str): The two-letter country code.
#         labels (list, optional): A list of labels for the fabric. Defaults to [].
#         topology (str, optional): The fabric topology (MESH or SPINE_LEAF). Defaults to None.

#     Returns:
#         dict: JSON response containing the created fabric information, or None on error.
#     """

#     fabric_data = {
#         "name": fabric_name,
#         "description": description,
#         "location": location,
#         "address": address,
#         "city": city,
#         "country": country,
#         "labels": labels,
#     }

#     if topology:
#       fabric_data["topology"] = topology

#     payload = {"fabrics": [fabric_data]}
#     url = f"{BASE_URL}/fabrics"
#     response = _make_post_request(auth, url, payload=payload)

#     return response

# # /fabrics/{fabricId}
# def get_fabric(auth, fabricId, candidate=None, include_metadata=False):
#     """
#     Retrieves a specific fabric.
#     Args:
#         fabricId (str): The ID or name of the fabric.
#         candidate (str, optional): The candidate configuration name. Defaults to None.
#         include_metadata (bool, optional): Include object metadata in the response. Defaults to False.
#     Returns:
#         dict: JSON response containing the fabric information, or None on error.
#     """
#     params = {}
#     if candidate:
#         params["candidate"] = candidate
#     if include_metadata:
#         params["includeMetadata"] = includeMetadata
#     response = _make_get_request(auth, f"{BASE_URL}/fabrics/{fabricId}", params=params)
#     return response

# def update_fabric(auth, fabricId, payload):
#     """
#     Updates a specific fabric.

#     Args:
#         fabricId (str): The ID or name of the fabric.
#         payload (dict): A JSON payload containing the updated fabric properties. The keys depend upon #/components/schemas/configFabric:
#           * name (str, optional):  The user-defined name of the fabric
#           * description (str, optional): The description of the fabric.
#           * location (str, optional): The location of the fabric.
#           * address (str, optional): The street address.
#           * city (str, optional): The city.
#           * country (str, optional): The two-letter country code.
#           * labels (list, optional): A list of labels for the fabric.

#         Example:
#         ```json
#         {
#           "name": "updated-fabric-name",
#           "description": "Updated fabric description",
#           "location": "Updated Location",
#           "address": "Updated Address",
#           "city": "Updated City",
#           "country": "US",
#           "labels": ["label1", "label2"],
#           "topology": "SPINE_LEAF"
#         }
#         ```
#     Returns:
#         dict: JSON response containing the updated fabric information, or None on error.
#     """
#     response = _make_put_request(auth, f"{BASE_URL}/fabrics/{fabricId}", payload=payload)
#     return response

# def delete_fabric(auth, fabricId):
#     """
#     Deletes a specific fabric.
#     Args:
#         fabricId (str): The ID or name of the fabric to delete.
#     Returns:
#         int: HTTP status code, or None on error.
#     """
#     response = _make_delete_request(auth, f"{BASE_URL}/fabrics/{fabricId}")
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

# /fabrics/{fabricId}/connections
def get_fabric_connections(auth, fabricId, candidate=None):
    """
    Retrieves a list of connections within a fabric.

    Args:
        fabricId (str): The ID or name of the fabric.
        candidate (str, optional): The candidate configuration name. Defaults to None.

    Returns:
        dict: JSON response, or None on error.
    """
    params = {}
    if candidate:
        params["candidate"] = candidate
    response = _make_get_request(auth, f"{BASE_URL}/fabrics/{fabricId}/connections", params=params)
    return response

def add_fabric_connections(auth, fabricId, connections):
    """
    Adds one or more connections to a fabric.

    Args:
        fabricId (str): The ID or name of the fabric.
        connections (list): A list of connections to add.
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
              },
              {
                "local": {
                  "portName": "Ethernet1_22",
                  "nodeName": "node-leaf1"
                },
                "remote": {
                  "portName": "Ethernet1_22",
                  "nodeName": "node-spine0"
                }
              }
            ]
            ```
    Returns:
        dict: JSON response, or None on error.
    """
    payload = {"connections": connections}
    response = _make_post_request(auth, f"{BASE_URL}/fabrics/{fabricId}/connections", payload=payload)
    return response

def set_fabric_connections(auth, fabricId, connections):
    """
    Replaces all connections in a fabric with a new set of connections.

    Args:
        fabricId (str): The ID or name of the fabric.
        connections (list): A list of connections to set.

    Returns:
        dict: JSON response, or None on error.
    """
    payload = {"connections": connections}
    response = _make_put_request(auth, f"{BASE_URL}/fabrics/{fabricId}/connections", payload=payload)
    return response

def delete_fabric_connections(auth, fabricId):
    """
    Deletes all connections in the fabric.
    Args:
        fabricId (str): The ID or name of the fabric.
    """
    response = _make_delete_request(auth, f"{BASE_URL}/fabrics/{fabricId}/connections")
    return response

# /fabrics/{fabricId}/connections/{connectionId}
def get_fabric_connection(auth, fabricId, connectionId, candidate=None):
    """
    Retrieves a specific connection by ID.

    Args:
        fabricId (str): The ID or name of the fabric.
        connectionId (str): The ID of the connection.
        candidate (str, optional):  Candidate configuration name. Defaults to None.

    Returns:
        dict: JSON response, or None on error.
    """
    params = {}
    if candidate:
        params["candidate"] = candidate
    response = _make_get_request(auth, f"{BASE_URL}/fabrics/{fabricId}/connections/{connectionId}", params=params)
    return response

def delete_fabric_connection(auth, fabricId, connectionId):
  """
    Delete a specific connection.
    Args:
        fabricId (str): The ID or name of the fabric.
        connectionId (str): The ID of the connection.
    """
  response = _make_delete_request(auth, f"{BASE_URL}/fabrics/{fabricId}/connections/{connectionId}")
  return response

# /fabrics/{fabricId}/nodes
def get_fabric_nodes(auth, fabricId, candidate=None, includeMetadata=None):
    """
    Retrieves a list of nodes within a fabric.

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
    response = _make_get_request(auth, f"{BASE_URL}/fabrics/{fabricId}/nodes", params=params)
    return response

def add_fabric_nodes(auth, fabric_name, nodes):
    """
    Adds one or more nodes to a fabric.

    Args:
        fabricId (str): The ID or name of the fabric.
        nodes (list): A list of node objects to add.
         Example:
            ```json
             [
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
              },
              {
               "name": "node-leaf1",
               "description": "example fabric node leaf one",
               "enabled": true,
               "serialNumber": "RESTAA2001",
               "modelName": "HF6100-32D"
              },
             ]
            ```
    Returns:
        dict: JSON response, or None on error.
    """
    payload = {"nodes": nodes}
    response = _make_post_request(auth, f"{BASE_URL}/fabrics/{fabric_name}/nodes", payload=payload)
    return response

# /fabrics/{fabricId}/nodes/{nodeId}
def get_fabric_node(auth, fabricId, nodeId, candidate=None, includeMetadata=None):
    """
    Retrieves a specific node by ID or name.

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
    response = _make_get_request(auth, f"{BASE_URL}/fabrics/{fabricId}/nodes/{nodeId}", params=params)
    return response

def update_fabric_node(auth, fabricId, nodeId, payload):
    """
    Updates a specific node.

    Args:
        fabricId (str): The ID or name of the fabric.
        nodeId (str): The ID or name of the node.
        payload (dict): A JSON payload containing the updated node properties.

    Returns:
        dict: JSON response, or None on error.
    """
    response = _make_put_request(auth, f"{BASE_URL}/fabrics/{fabricId}/nodes/{nodeId}", payload=payload)
    return response

def delete_fabric_node(auth, fabricId, nodeId):
    """
    Deletes a specific node.

    Args:
        fabricId (str): The ID or name of the fabric.
        nodeId (str): The ID or name of the node.

    Returns:
        int: HTTP status code, or None on error.
    """
    response = _make_delete_request(auth, f"{BASE_URL}/fabrics/{fabricId}/nodes/{nodeId}")
    return response
# /fabrics/{fabricId}/nodes/{nodeId}/devices/{deviceId}
def bind_device(auth, fabricId, nodeId, deviceId):
    """
    Binds a device to a specific node
     Args:
        fabricId (str): The ID or name of the fabric.
        nodeId (str): The ID or name of the node.
        deviceId (str): The serial of the device.

    Returns:
         dict: JSON response or None on Error
    """
    response = _make_put_request(auth, f"{BASE_URL}/fabrics/{fabricId}/nodes/{nodeId}/devices/{deviceId}")
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

# /fabrics/{fabricId}/nodes/{nodeId}/managementPorts
def get_management_ports(auth, fabricId, nodeId, candidate=None, includeMetadata=None):
    """
    Retrieves a list of management ports for a specific node.
    Args:
        fabricId (str): The ID or name of the fabric.
        nodeId (str): The ID or name of the node.
        candidate (str, optional): The candidate configuration name. Defaults to None.
        includeMetadata (bool, optional): Include object metadata in the response. Defaults to False.
    Returns:
        dict: JSON response containing the list of management ports, or None on error.
    """
    params = {}
    if candidate:
        params["candidate"] = candidate
    if includeMetadata:
        params["includeMetadata"] = includeMetadata

    response = _make_get_request(auth, f"{BASE_URL}/fabrics/{fabricId}/nodes/{nodeId}/managementPorts", params=params)
    return response

def add_management_ports(auth, fabricId, nodeId, ports):
    """
    Creates or updates one or more ManagementPorts for a fabric node

    Args:
        fabricId (str): The ID or name of the fabric.
        nodeId (str):  The node id or name from which a device is bound.
        ports (list): A list of one or more ports to update.
              Example payload:
              ```json
               [
                 {
                  "name": "eth0",
                  "ipv4Address": "10.1.1.250/31",
                  "ipv4Gateway": "10.1.1.251",
                  "ipv6Address": "2a02:1243:5687:0:9c09:2c7a:7c78:9ffc/64",
                  "ipv6Gateway": "2a02:1243:5687:0:8d91:ba6b:b24d:9b41",
                  "dnsAddresses": [
                   "8.8.8.8",
                   "8.8.4.4"
                  ],
                  "proxyAddress": "https://10.1.1.10:8080",
                  "proxyUsername": "admin",
                  "proxyPassword": "admin123",
                  "enabled": true,
                  "cloudUrls": [
                   "https://a.b.com"
                  ],
                  "setProxyPassword": true,
                  "noProxy": [
                   "10.0.0.0/8",
                   "68.0.0.0/8",
                   "72.0.0.0/8",
                   "172.0.0.0/8",
                   "172.0.0.0/8",
                   "173.0.0.0/8",
                   "cisco.com",
                   "localhost",
                   "127.0.0.1",
                   ".local"
                  ]
                 }
                ]
              ```

    Returns:
        dict: JSON response
    """
    payload = {"ports": ports}
    response =_make_post_request(auth,
            f"{BASE_URL}/fabrics/{fabricId}/nodes/{nodeId}/managementPorts",payload=payload)
    return response

# /fabrics/{fabricId}/nodes/{nodeId}/managementPorts/{id}
def get_management_port(auth, fabricId, nodeId, id, candidate=None, includeMetadata=None):
    """
    Retrieves information on the management port specified

    Args:
        fabricId (str): The ID or name of the fabric.
        nodeId (str):  The node id or name from which a device is bound.
        id (str): ID of the port

    Returns:
        dict: JSON response
    """
    params = {}
    if candidate:
        params["candidate"] = candidate
    if includeMetadata:
        params["includeMetadata"] = includeMetadata
    response = _make_get_request(auth, f"{BASE_URL}/fabrics/{fabricId}/nodes/{nodeId}/managementPorts/{id}", params=params)
    return response

def update_management_port(auth, fabricId, nodeId, id, payload):
    """
    Updates the settings on a management port

    Args:
        fabricId (str): The ID or name of the fabric.
        nodeId (str):  The node id or name from which a device is bound.
        ports (list): A list of one or more ports to update.

    Returns:
        dict: JSON response
    """
    response = _make_put_request(auth, f"{BASE_URL}/fabrics/{fabricId}/nodes/{nodeId}/managementPorts/{id}", payload=payload)
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

# /fabrics/{fabricId}/nodes/{nodeId}/ports/{portId}
def get_port(auth, fabricId, nodeId, portId, candidate=None, includeMetadata=None):
    """
    Retrieves a specific port by its ID.

    Args:
        fabricId (str): The ID or name of the fabric.
        nodeId (str): The ID or name of the node.
        portId (str): The ID of the port.
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
    response = _make_get_request(auth, f"{BASE_URL}/fabrics/{fabricId}/nodes/{nodeId}/ports/{portId}", params=params)
    return response

def update_port(auth, fabricId, nodeId, portId, payload):
    """
    Updates a specific port.

    Args:
        fabricId (str): The ID or name of the fabric.
        nodeId (str): The ID or name of the node.
        portId (str): The ID of the port.
        payload (dict): A JSON payload containing the updated port properties.

    Returns:
        dict: JSON response, or None on error.
    """
    response = _make_put_request(auth, f"{BASE_URL}/fabrics/{fabricId}/nodes/{nodeId}/ports/{portId}", payload=payload)
    return response

def reset_port(auth, fabricId, nodeId, portId):
    """Resets a specific port

    Args:
        fabricId (str): The ID or name of the fabric.
        nodeId (str): The ID or name of the node.
        portId (str): The ID of the port.
    """
    response = _make_delete_request(auth, f"{BASE_URL}/fabrics/{fabricId}/nodes/{nodeId}/ports/{portId}")
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

def add_fabric_vnis(auth, fabricId, vnis):
    """
    Adds one or more VNIs to a fabric.

    Args:
        fabricId (str): The ID or name of the fabric.
        vnis (list): A list of VNI objects to add. Each VNI object must conform to the `#/components/schemas/modelsVni` schema.
            Example:
            ```json
            [
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
              },
              {
                "name": "vni-example-1002",
                "description": "Example VNI 2, no SVI",
                "vni": 1002,
                "vrfId": "1234-4567-7890-abcd"
              }
            ]
            ```

    Returns:
        dict: JSON response, or None on error.
    """
    payload = {"vnis": vnis}
    response = _make_post_request(auth, f"{BASE_URL}/fabrics/{fabricId}/vnis", payload=payload)
    return response

# /fabrics/{fabricId}/vnis/{vniId}
def get_fabric_vni(auth, fabricId, vniId, candidate=None, includeMetadata=None):
    """
    Retrieves a specific VNI by ID or name.

    Args:
        fabricId (str): The ID or name of the fabric.
        vniId (str): The ID or name of the VNI.
        candidate (str, optional): The candidate configuration name. Defaults to None.
        includeMetadata (bool, optional): Include object Metadata in the response. Defaults to False.

    Returns:
        dict: JSON response, or None on error.
    """
    params = {}
    if candidate:
        params["candidate"] = candidate
    if includeMetadata:
        params["includeMetadata"] = includeMetadata
    response = _make_get_request(auth, f"{BASE_URL}/fabrics/{fabricId}/vnis/{vniId}", params=params)
    return response

def update_fabric_vni(auth, fabricId, vniId, payload):
    """
    Updates a specific VNI.

    Args:
        fabricId (str): The ID or name of the fabric.
        vniId (str): The ID or name of the VNI.
        payload (dict): A JSON payload containing the updated VNI properties.

    Returns:
        dict: JSON response, or None on error.
    """
    response = _make_put_request(auth, f"{BASE_URL}/fabrics/{fabricId}/vnis/{vniId}", payload=payload)
    return response

def delete_fabric_vni(auth, fabricId, vniId):
   """
    Deletes a VNI given its ID

     Args:
        fabricId (str): The ID or name of the fabric.
        vniId (str, optional): The name for the device you are listing deleting a VNI device
   """
   response = _make_delete_request(auth, f"{BASE_URL}/fabrics/{fabricId}/vnis/{vniId}")
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

def add_fabric_vrfs(auth, fabricId, vrfs):
    """
    Creates or updates one or more Vrf with a specific name

    Args:
        fabricId (str): The ID or name of the fabric.
        vnis (list): Each VRF objects must conform to the `#/components/schemas/modelsVrf`.
           Example:
           ```json
           [
             {
              "name": "Vrf-exampleOne",
              "enabled": true
             },
             {
              "name": "Vrf-exampleTwo",
              "description": "Test Vrf for example-fabric",
              "labels": [
               "VRF_LABEL_ONE",
               "vrf_label_two",
               "vrf label three"
              ],
              "enabled": true
             },
             {
              "name": "Vrf-exampleThree",
              "enabled": true
             }
           ]
           ```

    Returns:
        dict: JSON response, or None on error.
    """
    payload = {"vrfs": vrfs}
    response = _make_post_request(auth,f"{BASE_URL}/fabrics/{fabricId}/vrfs", payload=payload)
    return response

# /fabrics/{fabricId}/vrfs/{vrfId}
def get_fabric_vrf(auth, fabricId, vrfId, candidate=None, includeMetadata=None):
    """
        Gets details for a vrf

        Args:
            fabricId (str): The ID or name of the fabric.
            vrfId (str): A list of user-defined labels that can be used for grouping and filtering VRFs.
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
    response = _make_get_request(auth, f"{BASE_URL}/fabrics/{fabricId}/vrfs/{vrfId}", params=params)
    return response

def update_fabric_vrf(auth, fabricId, vrfId, payload):
    """
        Updates a specific Vrf

        Args:
            fabricId (str): The ID or name of the fabric.
            vrfId (str): A list of user-defined labels that can be used for grouping and filtering VRFs.
            payload (str, optional): The Route Payload Defaults to None

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
    """
    response = _make_put_request(auth, f"{BASE_URL}/fabrics/{fabricId}/vrfs/{vrfId}", payload=payload)
    return response

def delete_fabric_vrf(auth, fabricId, vrfId):
    """
       Deletes a specific Vrf object.
       Args:
          fabricId (str): The ID or name of the fabric.
          vrfId (str): A list of user-defined labels that can be used for grouping and filtering VRFs.
    """
    response = _make_delete_request(auth, f"{BASE_URL}/fabrics/{fabricId}/vrfs/{vrfId}")
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

def add_fabric_static_routes(auth, fabricId, vrfId, staticRoutes):
    """
        Creates or updates one or more static route for a fabric vrf object

        Args:
            fabricId (str): The ID or name of the fabric.
            vrfId (str): A list of user-defined labels that can be used for grouping and filtering VRFs.
            staticRoutes (str, optional): Payload which creates or updates the static route. Defaults to None

    Returns:
        dict: JSON response, or None on error.

     **staticRoutes** example payload:
        ```json
        [
        {
          "name": "Vrf-exampleOne-SR1",
          "enabled": true,
          "routes": [
            {
              "prefix": "10.10.10.0/24",
              "preference": 10,
              "discard": true
            },
            {
              "prefix": "11.10.10.0/24",
              "preference": 10,
              "discard": true
            }
          ]
        }
       ]

        ```

    """
    payload = {"staticRoutes": staticRoutes}
    response = _make_post_request(auth,f"{BASE_URL}/fabrics/{fabricId}/vrfs/{vrfId}/staticRoutes",payload=payload)
    return response

# /fabrics/{fabricId}/vrfs/{vrfId}/staticRoutes/{routeId}
def get_fabric_static_route(auth, fabricId, vrfId, routeId, candidate=None, includeMetadata=None):
    """
     Gets information for a single fabric static Route

     Args:
         fabricId (str): The ID or name of the fabric.
         vrfId (str): A list of user-defined labels that can be used for grouping and filtering VRFs.
         routeId (str, optional): The name for the device you are listing information for. Defaults to None

    Returns:
        int: JSON response on success or None on Fail
    """
    params = {}
    if candidate:
        params["candidate"] = candidate
    if includeMetadata:
        params["includeMetadata"] = includeMetadata
    response = _make_get_request(auth, f"{BASE_URL}/fabrics/{fabricId}/vrfs/{vrfId}/staticRoutes/{routeId}", params=params)
    return response

def update_fabric_static_route(auth, fabricId, vrfId, routeId, payload):
    """
     Updates a specific static route for a given VRF object

     Args:
         fabricId (str): The ID or name of the fabric.
         vrfId (str): A list of user-defined labels that can be used for grouping and filtering VRFs.
         routeId (str, optional): The name for the device you are listing information for. Defaults to None
         payload (str, optional): The Route Payload Defaults to None
    """
    response = _make_put_request(auth, f"{BASE_URL}/fabrics/{fabricId}/vrfs/{vrfId}/staticRoutes/{routeId}", payload=payload)
    return response

def delete_fabric_static_route(auth, fabricId, vrfId, routeId):
   """
    Deletes a static route for a vrf ID in a fabric

     Args:
         fabricId (str): The ID or name of the fabric.
         vrfId (str): A list of user-defined labels that can be used for grouping and filtering VRFs.
         routeId (str, optional): The name for the device you are listing information for. Defaults to None
   """
   response = _make_delete_request(auth, f"{BASE_URL}/fabrics/{fabricId}/vrfs/{vrfId}/staticRoutes/{routeId}")
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