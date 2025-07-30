import sys
import json
import logging
import requests
from ruamel.yaml import YAML
from scripts.hyperfabric_api import get_fabric_configurations

# Setup logger
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

with open("schemas/validation/new_validation_with_desc_.json") as f:
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

def filter_attributes(obj, allowed_keys):
    """Return a dict containing only the allowed keys, in the same order."""
    return {k: obj[k] for k in allowed_keys if k in obj}

def filter_unused_ports(ports):
    return [port for port in ports if port.get("roles", [None])[0] != "UNUSED_PORT"]

def attach_static_routes(data):
    static_routes = data.pop("staticRoutes")
    vrfs = data.get("vrfs", [])

    for vrf in vrfs:
        vrf_name = vrf.get("name")
        if not vrf_name:
            continue
        matching_routes = [route for route in static_routes if route.get("vrfId") == vrf_name]
        if matching_routes:
            vrf["staticRoutes"] = matching_routes

def restructure_yaml(data):
    fabric_section = data.pop("fabric")

    overlap = set(data) & set(fabric_section)
    if overlap:
        print(f"Warning: overlapping keys: {overlap}")

    attach_static_routes(data)

    # Get schema-defined attribute orders
    fabric_keys = get_attribute_keys("fabrics")
    node_keys = get_attribute_keys("fabrics", "nodes")
    port_keys = get_attribute_keys("fabrics", "nodes", "ports")
    mgmt_keys = get_attribute_keys("fabrics", "nodes", "managementPorts")
    conn_keys = get_attribute_keys("fabrics", "connections")
    vni_keys = get_attribute_keys("fabrics", "vnis")
    vrf_keys = get_attribute_keys("fabrics", "vrfs")
    static_route_keys = get_attribute_keys("fabrics", "vrfs", "staticRoutes")

    reordered = {}

    # Add top-level fabric attributes
    for key in fabric_keys:
        if key in fabric_section:
            reordered[key] = fabric_section[key]

    # Reorder and add nested lists
    if "nodes" in data:
        reordered["nodes"] = []
        for node in data["nodes"]:
            filtered_node = filter_attributes(node, node_keys)
            if "managementPorts" in node:
                filtered_node["managementPorts"] = [
                    filter_attributes(p, mgmt_keys) for p in node["managementPorts"]
                ]
            if "ports" in node:
                filtered_node["ports"] = [
                    filter_attributes(p, port_keys) for p in node["ports"]
                ]
                filtered_node["ports"] = filter_unused_ports(filtered_node["ports"])
            reordered["nodes"].append(filtered_node)

    if "connections" in data:
        reordered["connections"] = [
            filter_attributes(c, conn_keys) for c in data["connections"]
        ]

    if "vnis" in data:
        reordered["vnis"] = [
            filter_attributes(v, vni_keys) for v in data["vnis"]
        ]

    if "vrfs" in data:
        reordered["vrfs"] = []
        for vrf in data["vrfs"]:
            filtered_vrf = filter_attributes(vrf, vrf_keys)
            if "staticRoutes" in vrf:
                filtered_vrf["staticRoutes"] = [
                    filter_attributes(sr, static_route_keys) for sr in vrf["staticRoutes"]
                ]
            reordered["vrfs"].append(filtered_vrf)

    return {"fabrics": [reordered]}

def main(fabric_name):
    fabric_data = {
        "name": fabric_name
    }
    try:
        response = get_fabric_configurations(fabric_data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        response = None 
    except Exception as e:
        print(f"Unexpected error: {e}")
        response = None
    
    output_path = f"output/{fabric_name}.yaml"
    output_path_json = f"output/{fabric_name}.json"
    if response is not None:
        try:
            data = response.json()
            yaml = YAML()
            yaml.indent(sequence=4, offset=2) 
            yaml.default_flow_style = False
            if data is not None:
                data = restructure_yaml(data)
            with open(output_path, "w") as f:
                yaml.dump(data, f)
            with open(output_path_json, "w") as f:
                json.dump(data, f, indent=2)
            print(f"Saved YAML to {output_path}")
        except Exception as e:
            print(f"Failed to write YAML: {e}")
            
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <fabric_name>")
        sys.exit(1)

    fabric_name = sys.argv[1]
    main(fabric_name)