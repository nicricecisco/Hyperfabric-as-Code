import json
from entities.definitions import ENTITY_PATHS
from utils.schema_loader import get_schema_path

def parse_attributes(obj, input_key):
    attributes = ATTRIBUTES[f"{input_key.upper()}"]
    pure = {key: obj[key] for key in obj if key in attributes}
    other = {key: obj[key] for key in obj if key not in attributes}

    return pure, other

schema_path = get_schema_path()
with open(schema_path) as f:
    schema = json.load(f)

EXCLUDE_ATTR = ["fabrics", "nodes", "managementPorts", "ports", "connections", "vnis", "vrfs", "staticRoutes", "autocabling", "delete", "bind"]

def _get_attribute_keys(*args):
    result = schema.get("properties", {})
    for item in args:
        # Safely get the next level dict
        next_level = result.get(item)
        if next_level is None:
            # Key not found, return empty list or raise error as you prefer
            return []
        result = next_level.get("items", {}).get("properties", {})
    keys = list(result.keys())
    return [attr for attr in keys if attr not in EXCLUDE_ATTR]


FABRIC_ATTRIBUTES = _get_attribute_keys(*ENTITY_PATHS["FABRIC"])
NODE_ATTRIBUTES = _get_attribute_keys(*ENTITY_PATHS["NODE"])
MGMT_PORT_ATTRIBUTES = _get_attribute_keys(*ENTITY_PATHS["MGMT_PORT"])
PORT_ATTRIBUTES = _get_attribute_keys(*ENTITY_PATHS["PORT"])
CONNECTION_ATTRIBUTES = _get_attribute_keys(*ENTITY_PATHS["CONNECTION"])
VNI_ATTRIBUTES = _get_attribute_keys(*ENTITY_PATHS["VNI"])
VRF_ATTRIBUTES = _get_attribute_keys(*ENTITY_PATHS["VRF"])
STATIC_ROUTE_ATTRIBUTES = _get_attribute_keys(*ENTITY_PATHS["STATIC_ROUTE"])

ATTRIBUTES = {
    "FABRIC": FABRIC_ATTRIBUTES,
    "NODE": NODE_ATTRIBUTES,
    "MGMT_PORT": MGMT_PORT_ATTRIBUTES,
    "PORT": PORT_ATTRIBUTES,
    "CONNECTION": CONNECTION_ATTRIBUTES,
    "VNI": VNI_ATTRIBUTES,
    "VRF": VRF_ATTRIBUTES,
    "STATIC_ROUTE": STATIC_ROUTE_ATTRIBUTES
}
