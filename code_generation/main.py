import sys
import ast
import astunparse
import subprocess
from ruamel.yaml import YAML
from pprint import pprint
from utils.logger import get_logger
from entities.definitions import ENTITY_KEYS, ENTITY_PATHS
from code_generation.helpers import camel_to_screaming_snake

yaml = YAML()
yaml.default_flow_style = False

# Setup logger
logger = get_logger()

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

def add_entity(new_key, new_path):
    """
    Adds new object to ENTITY_KEYS and ENTITY_PATHS in entities/definitions.py
    Args:
        new_key (str): The key of the new object, directly as is in object_schema.yaml
        new_path ([str]): A list representing the path to the object
    """
    orig_key = new_key
    new_key = camel_to_screaming_snake(new_key, make_singular=True)
    with open(definitions_file, "r") as f:
        definitions_source = f.read()

    tree = ast.parse(definitions_source)
    for node in tree.body:
        # Modify ENTITY_KEYS list
        if isinstance(node, ast.Assign) and node.targets[0].id == "ENTITY_KEYS":
            # node.value is a List node
            keys = [elt.s for elt in node.value.elts]
            if new_key not in keys:
                keys.append(new_key)
                # Rebuild list node
                node.value.elts = [ast.Constant(value=k) for k in keys]
        
        # Modify ENTITY_PATHS dict
        if isinstance(node, ast.Assign) and node.targets[0].id == "ENTITY_PATHS":
            # node.value is a Dict node
            keys = node.value.keys
            values = node.value.values

            # Check if new key already exists
            if not any(k.s == new_key for k in keys):
                keys.append(ast.Constant(value=new_key))
                # Convert enw_path list to ast List node
                list_node = ast.List(elts=[ast.Constant(value=p) for p in new_path], ctx=ast.Load())
                values.append(list_node)
    
    new_source = astunparse.unparse(tree)
    with open(definitions_file, "w") as f:
        f.write(new_source)

    subprocess.run([sys.executable, "-m", "black", definitions_file])
    logger.info(f"[SUCCESS] Successfully added entity '{orig_key}' to ENTITY_KEYS and ENTITY_PATHS in file '{definitions_file}'")

def create_new_object(key, obj):
    parent_obj = obj[0].get("owner", "fabric")
    path = ENTITY_PATHS[camel_to_screaming_snake(parent_obj)] + [key]

    try:
        add_entity(key, path)
    except Exception as e:
        logger.error(f"Error adding entity '{key}' when writing to file '{definitions_file}'")

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
        create_new_object(key, schema_data[key])
    
if __name__ == "__main__":
    main()

