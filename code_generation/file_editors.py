import sys
import ast
import json
import astunparse
import subprocess
import copy
from pprint import pprint
from utils.logger import get_logger, log_success_green
from code_generation.helpers import camel_to_screaming_snake, find_key_path, get_nested
from code_generation.code_templates.api_function_calls import template_comment_header, template_args_entry, template_extract_id, template_single_portion_of_api_path, \
     template_get_all_call, template_post_call, template_get_call, template_put_call, template_delete_call

# Setup logger
logger = get_logger()

# Modifies entities/definitions.py
def add_entity_to_definitions_file(new_key, new_path, definitions_file):
    """
    Adds new object to ENTITY_KEYS and ENTITY_PATHS in entities/definitions.py
    Args:
        new_key (str): The key of the new object, directly as is in object_schema.yaml
        new_path (str[]): A list representing the path to the object
        definitions_file (str): The path to definitions.py
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

# Modifies schemas/validation/new_validation_with_desc.json
def insert_into_json_schema(schema_file, parent_key, new_key, new_value):
    """
    Find parent_key anywhere in schema and insert the new object under it.
    Args:
        schema_file (str): The path to new_validation_with_desc.json
        parent_key (str): The name of the new object's parent object
        new_key (str): The name of the new object
        new_value (dict): The contents of the new object
    """
    def restructure_new_obj(obj):
        copied_obj = copy.deepcopy(obj) # Ensure no modification of the original object
        copied_obj[0].pop("owner", None)
        new_obj = {
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {}
            }
        }

        # Eventually, if we read in a full description, we'll have to parse it and edit this part
        for attr in copied_obj[0]:
            new_obj["items"]["properties"][attr] = {
                "type": copied_obj[0][attr]
            }
        
        return new_obj

    # Format the object to be added to the json schema
    new_obj = restructure_new_obj(new_value)

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
        target["items"]["properties"][new_key] = new_obj
    # Or if it has direct "properties", insert there
    elif "properties" in target:
        target["properties"][new_key] = new_obj
    else:
        raise ValueError(f"No properties found under '{parent_key}'")
    
    with open(schema_file, "w") as f:
        json.dump(schema, f, indent=2)

    success_message = f"[SUCCESS] Successfully added entity '{new_key}' to json schema in file '{schema_file}'"
    log_success_green(logger, success_message)

# Modifies entities/attributes.py
def register_attributes(attributes_file, key):
    """
    Adds the object's key to EXCLUDE_ATTR, creates the new object's _ATTRIBUTES variable, and adds this to the ATTRIBUTES dictionary.
    Args:
        attributes_file (str): The path to attributes.py
        key (str): The name of the new object
    """
    def make_assign_node(var_name, entity_key):
        return ast.Assign(
            targets=[ast.Name(id=var_name, ctx=ast.Store())],
            value=ast.Call(
                func=ast.Name(id="_get_attribute_keys", ctx=ast.Load()),
                args=[
                    ast.Starred(
                        value=ast.Subscript(
                            value=ast.Name(id="ENTITY_PATHS", ctx=ast.Load()),
                            slice=ast.Constant(value=f"{entity_key}"),
                            ctx=ast.Load(),
                        ),
                        ctx=ast.Load(),
                    )
                ],
                keywords=[],
            ),
        )
    
    orig_key = key
    key = camel_to_screaming_snake(key, make_singular=True)
    key_attributes = key + "_ATTRIBUTES"
    inserted_variable = False

    with open(attributes_file, "r") as f:
        attributes_source = f.read()

    tree = ast.parse(attributes_source)
    for i, node in enumerate(tree.body):
        # Modify EXCLUDE_ATTR list
        if isinstance(node, ast.Assign) and node.targets[0].id == "EXCLUDE_ATTR":
            # node.value is a List node
            keys = [elt.s for elt in node.value.elts]
            if orig_key not in keys:
                keys.append(orig_key)
                # Rebuild list node
                node.value.elts = [ast.Constant(value=k) for k in keys]
        
        # Modify ATTRIBUTES dict
        if isinstance(node, ast.Assign) and node.targets[0].id == "ATTRIBUTES":
            # Create key_attributes variable first
            if not inserted_variable:
                tree.body.insert(i, make_assign_node(key_attributes, key))
                inserted_variable = True
            
            # node.value is a Dict node
            keys = node.value.keys
            values = node.value.values

            # Check if new key already exists
            if not any(k.s == key for k in keys):
                keys.append(ast.Constant(value=key))
                values.append(ast.Name(id=key_attributes, ctx=ast.Load()))
    
    new_source = astunparse.unparse(tree)
    with open(attributes_file, "w") as f:
        f.write(new_source)

    subprocess.run(
        [sys.executable, "-m", "black", attributes_file],
        capture_output=True,
        text=True
    )

    success_message = f"[SUCCESS] Successfully added entity '{key}' and its attributes to the ATTRIBUTES dictionary in '{attributes_file}'"
    log_success_green(logger, success_message)

# Modifies scripts/hyperfabric_api.py
def generate_api_function_calls(api_file, key, path_to_key):
    """
    Generates functions that make the API calls for the new object. These functions are based on the templates under code_generation/code_templates/api_function_calls.py
    Args:
        api_file (str): The path to hyperfabric_api.py
        key (str): The name of the new object
        path_to_key (str[]): A list of strings representing the complete path from the root object (fabrics) to the new object
    """

    with open(api_file, "r") as f:
        api_functions = f.read()
    
    tree = ast.parse(api_functions)
    filled_comment_header = template_comment_header.format(
        KEY_UPPER = camel_to_screaming_snake(key, make_singular=True)
    )

    template_tree = ast.parse(filled_comment_header)
    tree.body.extend(template_tree.body)

    new_code = ast.unparse(tree)
    with open(api_file, "w") as f:
        f.write(new_code)

