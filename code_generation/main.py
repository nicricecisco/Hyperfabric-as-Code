from ruamel.yaml import YAML
from pprint import pprint
from utils.logger import get_logger, log_error_red
from entities.definitions import ENTITY_KEYS, ENTITY_PATHS
from code_generation.helpers import camel_to_screaming_snake
from code_generation.file_editors import add_entity_to_definitions_file, insert_into_json_schema

yaml = YAML()
yaml.default_flow_style = False

# Setup logger
logger = get_logger()

# Global constants
NEW_OBJ_PATH = None

# ----------------- OBJECT SCHEMA -----------------
object_schema = "object_schema.yaml"

# ----------------- ENTITY FILES -----------------
attributes_file = "entities/attributes.py"
functions_file = "entities/functions.py"
definitions_file = "entities/definitions.py"

# ----------------- SCRIPTS -----------------
main_pipeline = "scripts/handle_json_input.py"
hyperfabric_api = "scripts/hyperfabric_api.py"

# ----------------- SCHEMA FILES -----------------
validation_json = "schemas/validation/new_validation_with_desc.json"
validation_template = "schemas/validation/validation_template.yaml"

def create_new_object(key, obj):
    global NEW_OBJ_PATH

    parent_obj = obj[0].get("owner", "fabric")
    NEW_OBJ_PATH = ENTITY_PATHS[camel_to_screaming_snake(parent_obj)] + [key]

    try:
        add_entity_to_definitions_file(key, NEW_OBJ_PATH, definitions_file)
    except Exception as e:
        logger.error(f"Error adding entity '{key}' when writing to file '{definitions_file}'")

def validate_new_object(key, obj):
    if not isinstance(obj, list):
        error_message = f"Object '{key}' must be a list but is currently a {type(obj).__name__}"
        log_error_red(logger, error_message)
        return False
    if len(obj) != 1:
        error_message = f"Object '{key}' must be a list of length 1 but is currently of length {len(obj)}"
        log_error_red(logger, error_message)
        return False
    
    obj_item = obj[0]
    is_invalid = False
    for attr in ("name", "owner"):
        if attr not in obj_item:
            error_message = f"Object '{key}' is missing the attribute: '{attr}'"
            log_error_red(logger, error_message)
            is_invalid = True

    if is_invalid:
        return False
    
    logger.info(f"Object '{key}' is valid")
    return True

def get_new_keys(schema_data):
    current_keys = set(ENTITY_KEYS)
    new_keys = []
    for key in schema_data:
        if camel_to_screaming_snake(key, make_singular=True) not in current_keys:
            new_keys.append(key)
    return new_keys

def read_in_schema():
    with open(object_schema, "r") as f:
        return yaml.load(f)

def main():
    schema_data = read_in_schema()
    new_keys = get_new_keys(schema_data)
    
    for key in new_keys:
        new_obj = schema_data[key]
        
        # Validate key
        is_valid = validate_new_object(key, new_obj)
        if not is_valid:
            return
        
        parent = new_obj[0]["owner"]
        
        # Begin modifying files
        create_new_object(key, new_obj) # Modifies entities/definitions.py
        insert_into_json_schema(validation_json, parent + "s", key, new_obj) # Modifies schemas/validation/new_validation_with_desc.json
        
    
if __name__ == "__main__":
    main()

