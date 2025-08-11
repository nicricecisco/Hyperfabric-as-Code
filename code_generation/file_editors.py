import sys
import ast
import json
import astunparse
import subprocess
from utils.logger import get_logger, log_success_green
from code_generation.helpers import camel_to_screaming_snake, find_key_path, get_nested

# Setup logger
logger = get_logger()

# Modifies entities/definitions.py
def add_entity_to_definitions_file(new_key, new_path, definitions_file):
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

    subprocess.run(
        [sys.executable, "-m", "black", definitions_file],
        capture_output=True,
        text=True
    )
    
    success_message = f"[SUCCESS] Successfully added entity '{orig_key}' to ENTITY_KEYS and ENTITY_PATHS in file '{definitions_file}'"
    log_success_green(logger, success_message)
    # logger.info(f"[SUCCESS] Successfully added entity '{orig_key}' to ENTITY_KEYS and ENTITY_PATHS in file '{definitions_file}'")

# Modifies schemas/validation/new_validation_with_desc.json
def insert_into_json_schema(schema_file, parent_key, new_key, new_value):
    """Find parent_key anywhere in schema and insert the new object under it."""
    with open(schema_file, "r") as f:
        schema = json.load(f)

    path = find_key_path(schema, parent_key)
    if not path:
        raise KeyError(f"Key '{parent_key}' not found in schema")

    # Navigate to the 'properties' dict of the parent
    target = get_nested(schema, path)
    if not isinstance(target, dict):
        raise TypeError(f"Target at '{parent_key}' is not a dict")

    # If it has an "items" with "properties", we insert there
    if "items" in target and "properties" in target["items"]:
        target["items"]["properties"][new_key] = new_value
    # Or if it has direct "properties", insert there
    elif "properties" in target:
        target["properties"][new_key] = new_value
    else:
        raise ValueError(f"No properties found under '{parent_key}'")
    
    with open(schema_file, "w") as f:
        json.dump(schema, f, indent=2)
