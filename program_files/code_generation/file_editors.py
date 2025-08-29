import sys
import ast
import json
import astunparse
import subprocess
import copy
import libcst as cst
import libcst.matchers as m
from pprint import pprint
from string import Template
from libcst import EmptyLine, Comment
from program_files.utils.logger import get_logger, log_success_green
from program_files.code_generation.helpers import camel_to_screaming_snake, find_key_path, get_nested
from program_files.code_generation.code_templates.api_function_calls import template_comment_header, template_args_entry, template_extract_id, template_single_portion_of_api_path, \
     template_get_all_call, template_post_call, template_get_call, template_put_call, template_delete_call
from program_files.code_generation.code_templates.entity_processing import template_comment_header_main, template_parent_id_entry, template_entity_processing_standard, template_entity_processing_fabric_child

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

# Modifies schemas/validation/new_validation_with_desc.json for a new object
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

# Modifies schemas/validation/new_validation_with_desc.json for a new attribute
def insert_new_attribute(schema_file, key, new_attributes):
    """
    Inserts new attributes for an existing object key
    Args:
        schema_file (str): The path to new_validation_with_desc.json
        key (str): The name of the existing object
        new_attributes ([dict]): List containing new attributes and their associated types
    """

    with open(schema_file, "r") as f:
        json_schema = json.load(f)

    if not json_schema:
        return

    path = find_key_path(json_schema, key)
    if not path:
        raise KeyError(f"Key '{key}' not found in schema")
    
    target = get_nested(json_schema, path)
    if not isinstance(target, dict):
        raise TypeError(f"Target at '{key}' is not a dict")

    for val in new_attributes:
        if "items" in target and "properties" in target["items"]:
            target["items"]["properties"][val] = {}
        # Or if it has direct "properties", insert there
        elif "properties" in target:
            target["properties"][val] = {}
        else:
            raise ValueError(f"No properties found under '{key}'")
        
    with open(schema_file, "w") as f:
        json.dump(json_schema, f, indent=2)

    success_message = f"[SUCCESS] Successfully added attributes {', '.join(new_attributes)} under {key} to json schema'"
    log_success_green(logger, success_message)

    return

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

    def generate_arg_list(indent=" " * 12):
        def join_id_list(items):
            if not items:
                return ""
            if len(items) == 1:
                return items[0]
            return ", ".join(items[:-1]) + ", and " + items[-1]
        
        arg_lines = []
        for i, obj_name in enumerate(path_to_key[:-1]):
            filled_args_entry = template_args_entry.substitute(
                KEY_A_PARENT_ID_SNAKE=(camel_to_screaming_snake(obj_name, make_singular=True).lower() + "_id"),
                KEY_A_PARENT_SINGULAR=obj_name[:-1]
            ).lstrip("\n")
            # Apply indentation to every line in this entry
            currIndent = "" if i == 0 else indent # Artifact of first line's indent being caused by default new line indentation
            indented_entry = "\n".join(currIndent + line if line.strip() else "" for line in filled_args_entry.splitlines())
            arg_lines.append(indented_entry)
        return "\n".join(arg_lines), join_id_list([p[:-1] + " ID" for p in path_to_key[:-1]])
    
    def generate_id_declarations(full=True, indent=" " * 4):
        id_declarations = []
        for i, obj_name in enumerate(path_to_key):
            filled_id_declarations = template_extract_id.substitute(
                KEY_A_PARENT_ID_CAMEL=obj_name[:-1] + "Id",
                KEY_A_PARENT_ID_SNAKE=(camel_to_screaming_snake(obj_name, make_singular=True).lower() + "_id"),
                KEY_DATA_OBJ=KEY_DATA_OBJ
            )
            # Apply indentation to every line in this entry
            currIndent = "" if i == -1 else indent # Not necessary, but here if the indenting issue arises
            indented_entry = "\n".join(currIndent + line if line.strip() else "" for line in filled_id_declarations.splitlines())
            id_declarations.append(indented_entry)
        id_declarations = id_declarations if full else id_declarations[:-1]
        return "".join(id_declarations)

    def generate_api_path(full=True):
        path = ""
        for i, obj_name in enumerate(path_to_key):
            placeholder = "" if not full and i == len(path_to_key) - 1 else f"/{{{obj_name[:-1]}Id}}"
            path += f"/{obj_name}{placeholder}"
        return path

    blank_line = cst.EmptyLine()
    screaming_snake_plural = camel_to_screaming_snake(key)
    KEY_DATA_OBJ = f"{screaming_snake_plural[:-1].lower()}_data_obj"

    with open(api_file, "r") as f:
        api_functions = f.read()
        
    # Create CST from the existing file
    module = cst.parse_module(api_functions)

    # Fill in comment template
    filled_comment_header = template_comment_header.format(
        KEY_UPPER=screaming_snake_plural.replace("_", " ")
    )

    arg_list, parent_id_list = generate_arg_list()
    api_path = generate_api_path(full=False)
    api_path_full = generate_api_path(full=True)
    id_declarations = generate_id_declarations(full=False)

    template_vars = {
        "KEY_CAMEL": key,
        "KEY_CAMEL_SINGULAR": key[:-1],
        "KEY_DATA_OBJ": KEY_DATA_OBJ,
        "KEY_LOWER_SNAKE_PLURAL": screaming_snake_plural.lower(),
        "KEY_LOWER_SNAKE_SINGULAR": screaming_snake_plural[:-1].lower(),
        "KEY_PARENT_ID_LIST": parent_id_list,
        "KEY_PARENT_SINGULAR": path_to_key[-2][:-1],
        "KEY_PATH_ROOT_TO_KEY": api_path,
        "KEY_PATH_ROOT_TO_KEY_FULL": api_path_full,
        "INSERT_PARENT_ARG_LIST": arg_list,
        "INSERT_TEMPLATE_EXTRACT_ID": id_declarations,
    }

    # Fill in all the function templates
    get_all_func = template_get_all_call.substitute(**template_vars)
    post_func = template_post_call.substitute(**template_vars)
    get_func = template_get_call.substitute(**template_vars)
    put_func = template_put_call.substitute(**template_vars)
    delete_func = template_delete_call.substitute(**template_vars)

    # String together all the blocks
    comment_line = EmptyLine(comment=Comment(filled_comment_header.strip()))
    comment_block = [blank_line, blank_line] + [comment_line] + [blank_line, blank_line]
    get_all_func_module = cst.parse_module(get_all_func)
    post_func_module = cst.parse_module(post_func)
    get_func_module = cst.parse_module(get_func)
    put_func_module = cst.parse_module(put_func)
    delete_func_module = cst.parse_module(delete_func)

    new_body = list(module.body) + comment_block + list(get_all_func_module.body) + [blank_line] + list(post_func_module.body) + [blank_line] + list(get_func_module.body) + [blank_line] + list(put_func_module.body) + [blank_line] + list(delete_func_module.body)

    # Parse the generated code into CST nodes
    updated_module = module.with_changes(body=new_body)

    # Write it back — all comments, spacing, and newlines preserved
    with open(api_file, "w") as f:
        f.write(updated_module.code)

    success_message = f"[SUCCESS] Successfully created API function calls and wrote them to {api_file}'"
    log_success_green(logger, success_message)

# Modifies entities/functions.py
def generate_function_object(functions_file, key):
    """
    Adds generated functions to FUNCTION_OBJECTS in entities/functions.py

    Args:
        functions_file (str): Path to functions.py
        key (str): Key of the new object
    """
    class AppendToHyperfabricImport(cst.CSTTransformer):
        def __init__(self, new_funcs):
            self.new_funcs = new_funcs

        def leave_ImportFrom(self, original_node, updated_node):
            if m.matches(
                original_node,
                m.ImportFrom(
                    module = m.Attribute(
                        value=m.Attribute(
                            value=m.Name("program_files"),
                            attr=m.Name("scripts"),
                        ),
                        attr=m.Name("hyperfabric_api"),
                    )
                ),
            ):
                current_names = list(updated_node.names)
                for func in self.new_funcs:
                    if not any(alias.name.value == func for alias in current_names):
                        current_names.append(cst.ImportAlias(name=cst.Name(func)))
                return updated_node.with_changes(names=current_names)
            return updated_node
    
    key_lower_snake = camel_to_screaming_snake(key, make_singular=True).lower()
    function_names = [f"get_fabric_{key_lower_snake}", f"add_fabric_{key_lower_snake}s", f"update_fabric_{key_lower_snake}", f"delete_fabric_{key_lower_snake}"]
    template_line = Template(
        "${key_lower_snake}_func_obj = _make_func_object(get_func=${get_func}, post_func=${post_func}, put_func=${put_func}, del_func=${del_func})"
    )

    with open(functions_file, "r") as f:
        api_functions = f.read()

    module = cst.parse_module(api_functions)

    new_module = module.visit(AppendToHyperfabricImport(function_names))

    template_vars = {
        "key_lower_snake": key_lower_snake,
        "get_func": function_names[0],
        "post_func": function_names[1],
        "put_func": function_names[2],
        "del_func": function_names[3]
    }
    func_obj_declaration = template_line.substitute(**template_vars)
    func_obj_module = cst.parse_module(func_obj_declaration)
    func_obj_node = func_obj_module.body[0]  # This is a SimpleStatementLine

    # Build new body by inserting before FUNCTION_OBJECTS assignment
    new_body = []
    inserted = False
    
    for stmt in new_module.body:
        if isinstance(stmt, cst.SimpleStatementLine):
            for i, small_stmt in enumerate(stmt.body):
                if isinstance(small_stmt, cst.Assign):
                    target = small_stmt.targets[0].target
                    if isinstance(target, cst.Name) and target.value == "FUNCTION_OBJECTS":
                        if not inserted:
                            new_body.append(func_obj_node)
                            inserted = True

                        if isinstance(small_stmt.value, cst.Dict):
                            new_entry = cst.DictElement(
                                key=cst.SimpleString(f'"{camel_to_screaming_snake(key, make_singular=True)}"'),
                                value=cst.Name(f"{key_lower_snake}_func_obj"),
                            )
                            new_elements = list(small_stmt.value.elements) + [new_entry]
                            updated_dict = small_stmt.value.with_changes(elements=new_elements)
                            updated_assign = small_stmt.with_changes(value=updated_dict)

                            # Replace the original small_stmt with the updated one
                            stmt = stmt.with_changes(body=[updated_assign])

        # Always append the (possibly updated) statement
        new_body.append(stmt)
    
    updated_module = new_module.with_changes(body=new_body)

    with open(functions_file, "w") as f:
        f.write(updated_module.code)
    
    subprocess.run(
        [sys.executable, "-m", "black", functions_file],
        capture_output=True,
        text=True
    )

    success_message = f"[SUCCESS] Successfully added {key} functions to {functions_file}'"
    log_success_green(logger, success_message)

# Modifies scripts/handle_json_input.py
def insert_entity_processing(main_file, key, parents):        
    class InsertAfterProcessEntity(cst.CSTTransformer):
        def __init__(self, entity_processing_body, parent):
            self.entity_processing_body = entity_processing_body
            self.parent_var = f"{parent}_other"
            self.parent = parent
            self.inside_target_func = False

        def visit_FunctionDef(self, node):
            if node.name.value == "_loop_through_attributes":
                self.inside_target_func = True

        def leave_FunctionDef(self, original_node, updated_node):
            if not self.inside_target_func:
                return updated_node

            self.inside_target_func = False

            if self.parent == "fabric":
                # Insert our block at the top of the function body
                comment_line = cst.EmptyLine(comment=cst.Comment(filled_comment_header.strip()))
                new_body = [blank_line, comment_line] + list(self.entity_processing_body.body) + list(updated_node.body.body)
                return updated_node.with_changes(
                    body=updated_node.body.with_changes(body=new_body)
                )

            return updated_node

        def leave_IndentedBlock(self, original_node, updated_node):
            if not self.inside_target_func or self.parent == "fabric":
                return updated_node

            # Otherwise: normal case, insert after <parent>_other = _process_entity(...)
            new_body = []
            for stmt in updated_node.body:
                new_body.append(stmt)
                if m.matches(
                    stmt,
                    m.SimpleStatementLine(
                        body=[
                            m.Assign(
                                targets=[m.AssignTarget(target=m.Name(self.parent_var))],
                                value=m.Call(func=m.Name("_process_entity"))
                            )
                        ]
                    )
                ):
                    comment_line = EmptyLine(comment=Comment(filled_comment_header.strip()))
                    comment_block = [blank_line, comment_line]
                    new_body.extend(comment_block)
                    new_body.extend(self.entity_processing_body.body)

            return updated_node.with_changes(body=new_body)

    
    def generate_id_list(indent):
        id_list = []
        for i in range(1, len(parents)):
            p = camel_to_screaming_snake(parents[i], make_singular=True).lower()
            id_str = template_parent_id_entry.substitute(
                A_PARENT_ID=f"{p}_id",
                A_PARENT_KEY_SNAKE=p
            ).strip("\n")
            space = indent if i != 1 else 0
            id_list.append(space * " " + id_str)
        return "\n".join(id_list)
    
    parent = parents[-1][:-1]
    parent_id_list = generate_id_list(indent=(len(parents)) * 4)

    # Prepare your entity processing snippet
    screaming_snake_plural = camel_to_screaming_snake(key)
    template_vars = {
        "KEY_DATA_OBJ": f"{screaming_snake_plural[:-1].lower()}_data_obj",
        "KEY_LOWER_SNAKE_SINGULAR": screaming_snake_plural[:-1].lower(),
        "KEY_NORMAL": key,
        "KEY_OTHER": f"{screaming_snake_plural[:-1].lower()}_other",
        "PARENT_ID_LIST": parent_id_list,
        "PARENT_OTHER": f"{camel_to_screaming_snake(parent).lower()}_other"
    }
    entity_processing = template_entity_processing_fabric_child.substitute(**template_vars) if parent == "fabric" else template_entity_processing_standard.substitute(**template_vars)
    entity_processing_module = cst.parse_module(entity_processing)

    with open(main_file, "r") as f:
        main_pipeline = f.read()

    blank_line = cst.EmptyLine()

    # Fill in comment template
    filled_comment_header = template_comment_header_main.format(
        KEY_UPPER=screaming_snake_plural.replace("_", " ")
    )

    module = cst.parse_module(main_pipeline)
    transformer = InsertAfterProcessEntity(entity_processing_module, camel_to_screaming_snake(parent).lower())
    new_module = module.visit(transformer)

    with open(main_file, "w") as f:
        f.write(new_module.code)

    success_message = f"[SUCCESS] Successfully added code to {main_file} to process '{key}' in main pipeline"
    log_success_green(logger, success_message)

# Modifies get_fabric_config.py
def add_code_to_fetch(extract_file, key, parents):
    pass