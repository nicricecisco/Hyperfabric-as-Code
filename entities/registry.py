from entities.attributes import ATTRIBUTES
from entities.functions import FUNCTION_OBJECTS

# Keys must match the ones used in ATTRIBUTES and FUNCTION_OBJECTS
ENTITY_KEYS = [
    "FABRIC",
    "NODE",
    "MGMT_PORT",
    "PORT",
    "CONNECTION",
    "VNI",
    "VRF",
    "STATIC_ROUTE"
]

def _build_entities(keys, attributes_map, functions_map):
    return {
        key: {
            "attributes": attributes_map.get(key),
            "func_obj": functions_map.get(key)
        }
        for key in keys
    }

def get_entity(key):
    return ENTITIES.get(f"{key.upper()}")

ENTITIES = _build_entities(ENTITY_KEYS, ATTRIBUTES, FUNCTION_OBJECTS)
