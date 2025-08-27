import sys
import json
from ruamel.yaml import YAML
from pprint import pprint
from program_files.utils.schema_loader import get_schema_path
from program_files.utils.logger import get_logger, log_error_red
from program_files.entities.definitions import ENTITY_KEYS, ENTITY_PATHS
from program_files.code_generation.helpers import camel_to_screaming_snake, find_key_path, get_nested
from program_files.code_generation.file_editors import add_entity_to_definitions_file, insert_into_json_schema, insert_new_attribute, register_attributes, \
    generate_api_function_calls, generate_function_object, insert_entity_processing, add_code_to_fetch

yaml = YAML()
yaml.default_flow_style = False

# Setup logger
logger = get_logger()

# ----------------- OBJECT SCHEMA -----------------
object_schema = "program_files/schemas/object_declaration.yaml"

# ----------------- ENTITY FILES -----------------
attributes_file = "program_files/entities/attributes.py"
functions_file = "program_files/entities/functions.py"
definitions_file = "program_files/entities/definitions.py"

# ----------------- SCRIPTS -----------------
main_pipeline = "program_files/scripts/handle_json_input.py"
hyperfabric_api = "program_files/scripts/hyperfabric_api.py"
get_fabric_config = "program_files/get_fabric_config.py"

# ----------------- SCHEMA FILE -----------------
validation_json = get_schema_path()

# ----------------- TEMPLATES -----------------
infra_template = "program_files/user_templates/infra_template.yaml"
tenant_template = "program_files/user_templates/tenant_template.yaml"

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

def get_new_attributes(schema_data, new_keys):
    def get_current_attributes(key):
        path = find_key_path(json_schema, key)
        target = get_nested(json_schema, path)
        if "items" not in target or "properties" not in target.get("items"):
            log_error_red(logger, f"Error trying to fetch current properties of {key} in {json_schema}")
            return None
        
        curr_attributes = []
        for attr in target["items"]["properties"]:
            curr_attributes.append(attr)
        return curr_attributes

    with open(validation_json, "r") as f:
        json_schema = json.load(f)
    
    if not json_schema:
        log_error_red(logger, f"Error reading in json schema: {json_schema}")
        sys.exit(1)
    
    result = {}
    for key, obj in schema_data.items():
        if key in new_keys:
            continue
        schema_attributes = get_current_attributes(key)
        declared_attributes = [attr for attr in obj[0] if attr != "owner"]
        new_attributes = [attr for attr in declared_attributes if attr not in schema_attributes]
        if len(new_attributes) > 0:
            result[key] = new_attributes # Instead of just the name, do a map of name: type

    return result

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
    # Before getting just the new keys, we should check the existing objects for new attributes
    new_keys = get_new_keys(schema_data)
    new_attributes = get_new_attributes(schema_data, new_keys)

    # Handles creating new attributes
    for key, obj in new_attributes.items():
        # Modifies schemas/validator.json
        insert_new_attribute(validation_json, key, obj)
    
    # Handles creating new objects
    for key in new_keys:
        new_obj = schema_data[key]
        
        # Validate key
        is_valid = validate_new_object(key, new_obj)
        if not is_valid:
            return
        
        parent = new_obj[0].get("owner", "fabric")
        new_obj_path = ENTITY_PATHS[camel_to_screaming_snake(parent)] + [key]
        
        # Begin modifying files
        # Modifies entities/definitions.py
        add_entity_to_definitions_file(key, new_obj_path, definitions_file)

        # Modifies schemas/validator.json
        insert_into_json_schema(validation_json, parent + "s", key, new_obj) 

        # Modifies entities/attributes.py
        register_attributes(attributes_file, key)

        # Modifies scripts/hyperfabric_api.py
        generate_api_function_calls(hyperfabric_api, key, new_obj_path)

        # Modifies entities/functions.py
        generate_function_object(functions_file, key)

        # Modifies scripts/handle_json_input.py
        insert_entity_processing(main_pipeline, key, new_obj_path[:-1])

        # Modifies get_fabric_config.py
        add_code_to_fetch(get_fabric_config, key, new_obj_path[:-1])
        
    
if __name__ == "__main__":
    main()

