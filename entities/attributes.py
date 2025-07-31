import json

def parse_attributes(obj, input_key):
    attributes = ATTRIBUTES[f"{input_key.upper()}"]
    pure = {key: obj[key] for key in obj if key in attributes}
    other = {key: obj[key] for key in obj if key not in attributes}

    return pure, other

with open("schemas/validation/new_validation_with_desc.json") as f:
    schema = json.load(f)

EXCLUDE_ATTR = ["fabrics", "nodes", "managementPorts", "ports", "connections", "vnis", "vrfs", "staticRoutes", "autocabling", "delete"]

def _get_attribute_keys(*args):
    result = schema.get("properties", {})
    for item in args:
        result = result.get(f"{item}").get("items", {}).get("properties", {})
    result = list(result.keys())
    return [attr for attr in result if attr not in EXCLUDE_ATTR]

FABRIC_OTHER_ATTRIBUTES = _get_attribute_keys("fabrics")
NODE_OTHER_ATTRIBUTES = _get_attribute_keys("fabrics", "nodes")
MGMT_PORT_OTHER_ATTRIBUTES = _get_attribute_keys("fabrics", "nodes", "managementPorts")
PORT_OTHER_ATTRIBUTES = _get_attribute_keys("fabrics", "nodes", "ports")
CONNECTION_OTHER_ATTRIBUTES = _get_attribute_keys("fabrics", "connections")
VNI_OTHER_ATTRIBUTES = _get_attribute_keys("fabrics", "vnis")
VRF_OTHER_ATTRIBUTES = _get_attribute_keys("fabrics", "vrfs")
STATIC_ROUTE_OTHER_ATTRIBUTES = _get_attribute_keys("fabrics", "vrfs", "staticRoutes")

ATTRIBUTES = {
    "FABRIC": FABRIC_OTHER_ATTRIBUTES,
    "NODE": NODE_OTHER_ATTRIBUTES,
    "MGMT_PORT": MGMT_PORT_OTHER_ATTRIBUTES,
    "PORT": PORT_OTHER_ATTRIBUTES,
    "CONNECTION": CONNECTION_OTHER_ATTRIBUTES,
    "VNI": VNI_OTHER_ATTRIBUTES,
    "VRF": VRF_OTHER_ATTRIBUTES,
    "STATIC_ROUTE": STATIC_ROUTE_OTHER_ATTRIBUTES
}