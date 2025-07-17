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

def describe_error(error: ValidationError):
    field_path = "/".join([str(p) for p in error.path]) or "(root)"
    user_value = error.instance
    base_msg = f"Error at '{field_path}' '{user_value}':"

    if error.validator == "pattern":
        pattern = error.validator_value
        explanation = REGEX_DESCRIPTIONS.get(pattern)
        if explanation:
            return f"{base_msg} {explanation}"
        else:
            return f"{base_msg} expected pattern {pattern}"

    elif error.validator == "type":
        expected_type = error.validator_value
        return f"{base_msg} expected type {expected_type}"

    elif error.validator == "enum":
        allowed = error.validator_value
        return f"{base_msg} must be one of '{allowed}'"

    elif error.validator in {"minimum", "maximum"}:
        limit = error.validator_value
        return f"{base_msg} value must be {error.validator} {limit}"

    elif error.validator in {"minLength", "maxLength"}:
        constraint = error.validator_value
        return f"{base_msg} string length must be {error.validator} {constraint}"

    elif error.validator == "required":
        missing = error.message
        return f"{base_msg} missing required field {missing}"

    return f"{base_msg} {error.message}"

def describe_error2(error: ValidationError, instance: dict):
    def resolve_path(path, root):
        """
        Walks the path and returns a list of named context elements like
        'fabric-name / node-name / port-name'. If no name is found, includes a snippet of the object.
        """
        path_parts = []
        current = root
        for part in path:
            if isinstance(part, int) and isinstance(current, list) and 0 <= part < len(current):
                current = current[part]
                if isinstance(current, dict):
                    name = current.get("name") or current.get("nodeName") or current.get("portName")
                    if name:
                        path_parts.append(str(name))
                    else:
                        # fallback to showing object summary
                        obj_str = str({k: v for k, v in current.items() if k in ("description", "type", "osType")})
                        path_parts.append(f"[unnamed {obj_str}]")
            elif isinstance(current, dict) and part in current:
                current = current[part]
        return "/".join(path_parts) or "(root)"

    field_path = resolve_path(error.path, instance)
    user_value = error.instance
    base_msg = f"Error at fabric '{field_path}' value '{user_value}':"

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
        missing_field = error.message  # already a readable message
        return f"{base_msg} {missing_field}"

    return f"{base_msg} {error.message}"




def validate_json(instance, schema):
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)
    if not errors:
        print("YAML is valid according to the JSON schema.")
    else:
        for e in errors:
            print(describe_error2(e, instance))
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
