from program_files.entities.definitions import ENTITY_KEYS
from program_files.entities.attributes import ATTRIBUTES
from program_files.entities.functions import FUNCTION_OBJECTS

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