import yaml
import json
import sys
from jsonschema import validate, ValidationError, Draft7Validator
from jsonschema.exceptions import best_match

REGEX_DESCRIPTIONS = {
    r"^(?!-)(?!\d+$)(?!-+$)[A-Za-z0-9-]+(?<!-)$": "allowed characters are letters, digits, hyphens and cannot start or end with a hyphen, cannot be only digits, and cannot be only hyphens" ,
    r"^eth\\([0-8]\\)$": "must be in the format 'eth(0)' to 'eth(8)'",
    r"^Ethernet1_([1-9]|[1-5][0-9]|6[0-4])$": "must be in the format 'Ethernet1_1' to 'Ethernet1_64'",
    r"^(1x40G\\(4\\)|1x100G\\(2\\)|1x100G\\(4\\)|1x200G\\(4\\)|1x400G|1x10G\\(1\\)|1x25G\\(1\\)|1x50G\\(1\\))$": "must be one of the specified port types: 1x40G(4), 1x100G(2), 1x100G(4), 1x200G(4), 1x400G, 1x10G(1), 1x25G(1), or 1x50G(1)",
    r"^(Default VRF|VRF[A-Za-z0-9]{1,100})$" : "must be either 'Default VRF' or 'VRF' followed by 1 to 100 alphanumeric characters"
}

def load_yaml_file(file_path):
    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)
        print("YAML file loaded successfully.")
        return data

def load_json_file(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
        print("JSON schema loaded successfully.")
        return data

def write_json(data, output_path):
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"JSON written to {output_path}")

def describe_error(error: ValidationError, instance: dict):
    def resolve_path(path, root):
        NAMING_KEYS = ["name", "nodeName", "portName", "vni", "vrf"]
        path_parts = []
        current = root
        prev_key = None

        for i, part in enumerate(path):
            # Handle list index: entering into an array of objects
            if isinstance(part, int) and isinstance(current, list) and 0 <= part < len(current):
                item = current[part]
                label = None
                for key in NAMING_KEYS:
                    if key in item:
                        label = str(item[key])
                        break

                if label:
                    # Replace the *last* added path key with key[label] format
                    if path_parts:
                        path_parts[-1] = f"{path_parts[-1]}[{label}]"
                    else:
                        path_parts.append(f"[{label}]")
                else:
                    # Fallback: insert object summary
                    summary = json.dumps(item, separators=(",", ":"), default=str)
                    summary = summary[:100] + "..." if len(summary) > 100 else summary
                    if path_parts:
                        path_parts[-1] = f"{path_parts[-1]}[{summary}]"
                    else:
                        path_parts.append(f"[{summary}]")
                current = item
                continue

            # Handle object key lookup
            if isinstance(current, dict) and part in current:
                path_parts.append(str(part))
                current = current[part]
                prev_key = part
            else:
                path_parts.append(str(part))

        return "/".join(path_parts) or "(root)"


    # Create a human-readable context path for the error
    field_path = resolve_path(error.path, instance)
    user_value = error.instance
    base_msg = f"Error at fabric '{field_path}' value '{user_value}':"

    # Match specific types of validation errors with friendly messages
    if error.validator == "pattern":
        pattern = error.validator_value
        explanation = REGEX_DESCRIPTIONS.get(pattern)
        if explanation:
            return f"{base_msg} {explanation}"
        else:
            return f"{base_msg} must match pattern {pattern}"

    elif error.validator == "type":
        expected_type = error.validator_value
        return f"{base_msg} expected type '{expected_type}'"

    elif error.validator == "enum":
        allowed = error.validator_value
        return f"{base_msg} must be one of {allowed}"

    elif error.validator in {"minimum", "maximum"}:
        limit = error.validator_value
        return f"{base_msg} value must be {error.validator} {limit}"

    elif error.validator in {"minLength", "maxLength"}:
        constraint = error.validator_value
        return f"{base_msg} string length must be {error.validator} {constraint}"

    elif error.validator == "required":
        # Already formatted error.message gives the missing field info
        missing_field = error.message
        return f"{base_msg} {missing_field}"

    # Fallback for any other types of validation errors
    return f"{base_msg} {error.message}"

def get_field_order(schema):
    """
    Recursively extract field order from a schema, including handling of allOf and anyOf.
    Returns a nested dict with field names mapped to sort index and substructure.
    """
    def merge_orders(orders):
        merged = {}
        for order in orders:
            for key, value in order.items():
                if key not in merged:
                    merged[key] = value
        return merged

    def recurse(subschema, path=()):
        order = {}

        if "properties" in subschema:
            for i, (key, value) in enumerate(subschema["properties"].items()):
                key_path = path + (key,)
                order[key] = {
                    "_index": i,
                    "_children": recurse(value, key_path)
                }

        elif "items" in subschema and isinstance(subschema["items"], dict):
            order = recurse(subschema["items"], path + ("[]",))

        elif "allOf" in subschema or "anyOf" in subschema:
            combined = subschema.get("allOf", []) + subschema.get("anyOf", []) + subschema.get("oneOf", [])
            all_orders = [recurse(s, path) for s in combined]
            order = merge_orders(all_orders)

        return order

    return recurse(schema)

def schema_sort_key(error, field_order):
    """
    Returns a tuple of indices representing the path to the error based on the schema-defined order.
    """
    path = list(error.absolute_path)
    key_path = [p if isinstance(p, str) else "[]" for p in path]

    order = field_order
    sort_key = []

    for key in key_path:
        if isinstance(order, dict) and key in order:
            sort_key.append(order[key].get("_index", float("inf")))
            order = order[key].get("_children", {})
        else:
            # Fallback for unknown keys or deeper-than-schema
            sort_key.append(float("inf"))

    return tuple(sort_key)

def check_for_duplicate_names(instance):
    """
    Check for duplicate names in the YAML content:
    - nodeName must be globally unique.
    - Other identifiers (name, vrfName, vniName, etc.) must be unique within each fabric.
    """
    errors = []
    global_node_names = set()

    def check_duplicates_in_list(items, key, seen, path):
        for idx, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            if key in item:
                val = item[key]
                if val in seen:
                    errors.append(f"Duplicate '{key}' value '{val}' found at {path}[{idx}]")
                else:
                    seen.add(val)

    fabrics = instance.get("fabrics", [])
    for fabric_idx, fabric in enumerate(fabrics):
        fabric_name = fabric.get("name", f"fabrics[{fabric_idx}]")
        fabric_path = f"fabrics[{fabric_name}]"

        # Check global uniqueness of node names
        nodes = fabric.get("nodes", [])
        for node_idx, node in enumerate(nodes):
            node_name = node.get("nodeName")
            if node_name:
                if node_name in global_node_names:
                    errors.append(f"Duplicate 'nodeName' value '{node_name}' found in {fabric_path}/nodes[{node_idx}]")
                else:
                    global_node_names.add(node_name)

        # Per-fabric duplicates
        fabric_scoped_keys = ["name", "vrfName", "vniName", "portName"]

        for key in fabric_scoped_keys:
            # Gather all objects where this key may appear
            def collect_objects(obj):
                if isinstance(obj, list):
                    for i in obj:
                        yield from collect_objects(i)
                elif isinstance(obj, dict):
                    if key in obj:
                        yield obj
                    for v in obj.values():
                        yield from collect_objects(v)

            seen = set()
            for obj in collect_objects(fabric):
                val = obj[key]
                if val in seen:
                    errors.append(f"Duplicate '{key}' value '{val}' found in {fabric_path}")
                else:
                    seen.add(val)

    return errors



def validate_json(instance, schema):
    field_order = get_field_order(schema)
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda e: schema_sort_key(e, field_order))
    dup_errors= check_for_duplicate_names(instance)
    if not errors:
        print("YAML is valid according to the JSON schema.")
    else:
        for msg in dup_errors:
            print(f"Duplicate name error: {msg}")
        for e in errors:
            print(describe_error(e, instance))
        sys.exit(1)


def main():
    if len(sys.argv) != 4:
        print("Usage: python validate_yaml.py input.yaml schema.json output.json")
        sys.exit(1)

    yaml_path = sys.argv[1]
    schema_path = sys.argv[2]
    json_output_path = sys.argv[3]

    # Load and convert
    yaml_data = load_yaml_file(yaml_path)
    json_schema = load_json_file(schema_path)
    write_json(yaml_data, json_output_path)

    # Validate
    validate_json(yaml_data, json_schema)
    print(f"Converted {yaml_path} to {json_output_path} and validated against {schema_path}.")

if __name__ == "__main__":
    main()
