import json
from utils.schema_loader import get_schema_path

def parse_attributes(obj, input_key):
    attributes = ATTRIBUTES[f"{input_key.upper()}"]
    pure = {key: obj[key] for key in obj if key in attributes}
    other = {key: obj[key] for key in obj if key not in attributes}

    return pure, other

schema_path = get_schema_path()
with open(schema_path) as f:
    schema = json.load(f)

EXCLUDE_ATTR = ["fabrics", "nodes", "managementPorts", "ports", "connections", "vnis", "vrfs", "staticRoutes", "autocabling", "delete"]

def _get_attribute_keys(*args):
    result = schema.get("properties", {})
    for item in args:
        result = result.get(f"{item}").get("items", {}).get("properties", {})
    result = list(result.keys())
    return [attr for attr in result if attr not in EXCLUDE_ATTR]

FABRIC_ATTRIBUTES = _get_attribute_keys("fabrics")
NODE_ATTRIBUTES = _get_attribute_keys("fabrics", "nodes")
MGMT_PORT_ATTRIBUTES = _get_attribute_keys("fabrics", "nodes", "managementPorts")
PORT_ATTRIBUTES = _get_attribute_keys("fabrics", "nodes", "ports")
CONNECTION_ATTRIBUTES = _get_attribute_keys("fabrics", "connections")
VNI_ATTRIBUTES = _get_attribute_keys("fabrics", "vnis")
VRF_ATTRIBUTES = _get_attribute_keys("fabrics", "vrfs")
STATIC_ROUTE_ATTRIBUTES = _get_attribute_keys("fabrics", "vrfs", "staticRoutes")

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