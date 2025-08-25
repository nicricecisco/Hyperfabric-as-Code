import sys
import json
import requests
from pprint import pprint
from ruamel.yaml import YAML
from program_files.utils.logger import get_logger
from program_files.utils.timestamp import generate_timestamp
from program_files.utils.schema_loader import get_schema_path
from program_files.utils.get_output_path import get_output_path
from program_files.scripts.hyperfabric_api import get_fabric, get_fabric_nodes, get_management_ports, get_ports, get_fabric_connections, get_fabric_vnis, get_fabric_vrfs, get_fabric_static_routes

logger = get_logger()

yaml = YAML()
yaml.indent(sequence=4, offset=2) 
yaml.default_flow_style = False

GET_CALLS = {
    "FABRIC": get_fabric,
    "NODE": get_fabric_nodes,
    "MGMT_PORT": get_management_ports,
    "PORT": get_ports,
    "CONNECTION": get_fabric_connections,
    "VNI": get_fabric_vnis,
    "VRF": get_fabric_vrfs,
    "STATIC_ROUTE": get_fabric_static_routes
}

with open(get_schema_path()) as f:
    schema = json.load(f)

def get_attribute_keys(*path):
    """Traverse the schema and return the attribute keys at the specified path."""
    result = schema.get("properties", {})
    for key in path:
        prop = result.get(key)
        if not prop:
            return []

        if prop.get("type") == "array":
            result = prop.get("items", {}).get("properties", {})
        else:
            result = prop.get("properties", {})

    return result

def restructure_annotations(obj):
    def restructure(annotations):
        new_obj = {}
        for annotation in annotations:
            new_obj[f"{annotation['name']}"] = annotation['value']
        return new_obj

    if isinstance(obj, dict):
        for key in list(obj.keys()):
            value = obj[key]
            if key == "annotations" and isinstance(value, list):
                obj[key] = restructure(value)
            elif isinstance(value, dict):
                restructure_annotations(value)
            elif isinstance(value, list):
                for item in value:
                    restructure_annotations(item)

def filter_unused_ports(ports):
    return [port for port in ports if port.get("roles", [None])[0] != "UNUSED_PORT"]

def filter_attributes(obj, allowed_attr_path):
    result = {}
    allowed_attr = get_attribute_keys(*allowed_attr_path)
    for attr in allowed_attr:
        if attr in obj:
            if isinstance(obj[attr], dict):
                new_path = allowed_attr_path + [attr]
                obj[attr] = filter_attributes(obj[attr], new_path)
            result[attr] = obj[attr]
    return result

def get_object(entity, data_obj, allowed_attr_path, key):
    try:
        logger.info(f"[GET {entity.upper()}] Making API request...")
        response = GET_CALLS[entity](data_obj)
        response.raise_for_status()
        result = response.json()
        if isinstance(result.get(key), list):
            filtered_items = []
            for item in result.get(key):
                filtered_items.append(filter_attributes(item, allowed_attr_path))
            return filtered_items
        return filter_attributes(result, allowed_attr_path) 
    except KeyError:
        logger.error(f"[GET_{entity}] Unknown entity type: '{entity}'", exc_info=True)
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"[GET_{entity}] HTTP error while retrieving {entity}: {http_err}", exc_info=True)
    except requests.exceptions.ConnectionError as conn_err:
        logger.error(f"[GET_{entity}] Connection error while retrieving {entity}: {conn_err}", exc_info=True)
    except requests.exceptions.Timeout as timeout_err:
        logger.error(f"[GET_{entity}] Timeout while retrieving {entity}: {timeout_err}", exc_info=True)
    except requests.exceptions.RequestException as req_err:
        logger.error(f"[GET_{entity}] Request exception while retrieving {entity}: {req_err}", exc_info=True)
    except Exception as e:
        logger.error(f"[GET_{entity}] Unexpected error while retrieving {entity}: {e}", exc_info=True)

    return None

def output_yaml(infra_result, tenant_result):
    infra_file_name = f"{fabric_name}-infra"
    tenant_file_name = f"{fabric_name}-tenant"
    infra_output_path = get_output_path(infra_file_name)
    tenant_output_path = get_output_path(tenant_file_name)

    now = generate_timestamp()
    comment = f"# Generated on {now}"
    if infra_result:        
        with open(infra_output_path, "w") as f:
            f.write(comment + "\n")
            yaml.dump(infra_result, f)
        logger.info(f"Saved YAML to {infra_output_path}")
    if tenant_result:        
        with open(tenant_output_path, "w") as f:
            f.write(comment + "\n")
            yaml.dump(tenant_result, f)
        logger.info(f"Saved YAML to {tenant_output_path}")
    else:
        logger.info(f"Nothing to output")

def main(fabric_name):
    # Get schema-defined attribute orders
    fabric_keys_path = ["fabrics"]
    node_keys_path = ["fabrics", "nodes"]
    mgmt_keys_path = ["fabrics", "nodes", "managementPorts"]
    port_keys_path = ["fabrics", "nodes", "ports"]
    conn_keys_path = ["fabrics", "connections"]
    vni_keys_path = ["fabrics", "vnis"]
    vrf_keys_path = ["fabrics", "vrfs"]
    static_route_keys_path = ["fabrics", "vrfs", "staticRoutes"]

    # -------------------- FABRIC --------------------
    fabric_data_obj = {
        "fabric": {
            "name": fabric_name
        }
    }
    fabric_result = get_object("FABRIC", fabric_data_obj, fabric_keys_path, "fabric")
    if not fabric_result:
        logger.error(f"No fabric with name '{fabric_name}' found.")    
        return  

    fabric_level_data_obj = {
        "fabric_id": fabric_name
    }

    # -------------------- NODES --------------------
    node_result = get_object("NODE", fabric_level_data_obj, node_keys_path, "nodes")
    if node_result:
        for node in node_result:
            node_level_data_obj = {
                "fabric_id": fabric_name,
                "node_id": node.get("name")
            }
            # -------------------- MANAGEMENT PORTS --------------------
            mgmt_port_result = get_object("MGMT_PORT", node_level_data_obj, mgmt_keys_path, "ports")
            if mgmt_port_result:
                node["managementPorts"] = mgmt_port_result

            # -------------------- PORTS --------------------
            port_result = get_object("PORT", node_level_data_obj, port_keys_path, "ports")
            if port_result:
                filtered_ports = filter_unused_ports(port_result) # We don't want to output all the unused ports
                if filtered_ports:
                    node["ports"] = filtered_ports

        fabric_result["nodes"] = node_result

    # -------------------- CONNECTIONS --------------------
    connection_result = get_object("CONNECTION", fabric_level_data_obj, conn_keys_path, "connections")
    if connection_result:
        fabric_result["connections"] = connection_result

    fabric_tenant = {}
    fabric_tenant["name"] = fabric_result["name"]
    # -------------------- VNIs --------------------
    vni_result = get_object("VNI", fabric_level_data_obj, vni_keys_path, "vnis")
    if vni_result:
        fabric_tenant["vnis"] = vni_result

    # -------------------- VRFs --------------------
    vrf_result = get_object("VRF", fabric_level_data_obj, vrf_keys_path, "vrfs")
    if vrf_result:
        for vrf in vrf_result:
            vrf_level_data_obj = {
                "fabric_id": fabric_name,
                "vrf_id": vrf.get("name")
            }

            # -------------------- STATIC ROUTES --------------------
            static_route_result = get_object("STATIC_ROUTE", vrf_level_data_obj, static_route_keys_path, "staticRoutes")
            if static_route_result:
                vrf["staticRoutes"] = static_route_result

        fabric_tenant["vrfs"] = vrf_result

    # In our schema, we define annotations as key: value as opposed to name: key, value: value
    restructure_annotations(fabric_result) 
    restructure_annotations(fabric_tenant)

    infra_result = {
        "fabrics": [fabric_result]
    }
    tenant_result = {
        "fabrics": [fabric_tenant]
    }
    
    return infra_result, tenant_result
    
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <fabric_name>")
        sys.exit(1)

    fabric_name = sys.argv[1]
    infra_result, tenant_result = main(fabric_name)

    output_yaml(infra_result, tenant_result)