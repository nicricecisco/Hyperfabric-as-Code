import json
from utils.schema_loader import get_schema_path
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from jsonschema import Draft7Validator, ValidationError
from typing import Any, Dict, List
"""
    from textual.app import App, ComposeResult
    from textual.containers import Horizontal
    from textual.widgets import Static, ScrollView
"""
from rich.text import Text
from rich.console import Console
from types import SimpleNamespace

REGEX_DESCRIPTIONS = {
    r"^(?!-)(?!\d+$)(?!-+$)[A-Za-z0-9-]+(?<!-)$":
        "allowed characters are letters and digits and hyphens, cannot start or end with a hyphen, cannot be only digits, and cannot be only hyphens",

    r"^([0-9A-Fa-f:]+)\\/(12[0-8]|1[01][0-9]|[1-9]?[0-9])$":
        "must be a valid ipv6 address with optional cidr subnet mask from 0 to 128",

    r"^Ethernet1_([1-9]|[1-5][0-9]|6[0-4])$":
        "must be in the format 'Ethernet1_1' to 'Ethernet1_64'",

    r"^(1x40G\\(4\\)|1x100G\\(2\\)|1x100G\\(4\\)|1x200G\\(4\\)|1x400G|1x10G\\(1\\)|1x25G\\(1\\)|1x50G\\(1\\))$":
        "must be one of the specified port types",

    r"^Vrf-?(?=.{1,15}$)(?!(?:\d{8,})$)[A-Za-z0-9]+$":
        "must be 'Vrf' optionally followed by a hyphen and 1 to 15 alphanumeric characters, with a limit of 7 digits if no letters",

    r"^(Default VRF|Vrf-?(?=.{1,15}$)(?!(?:\d{8,})$)[A-Za-z0-9]+)$":
        "must be either 'Default VRF' or 'Vrf' optionally followed by a hyphen, followed by 1 to 15 alphanumeric characters with a limit of 7 digits if no letters",

    r"^((25[0-5]|2[0-4]\\d|1\\d{2}|[1-9]?\\d)\\.){3}(25[0-5]|2[0-4]\\d|1\\d{2}|[1-9]?\\d)(\\/([0-9]|[1-2][0-9]|3[0-2]))?$":
        "must be a valid ipv4 address with optional cidr subnet mask from 0 to 32",

    r"^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}(/([0-9]|[1-9][0-9]|1[01][0-9]|12[0-8]))?$|^(([0-9a-fA-F]{1,4}:){1,7}:|:((:[0-9a-fA-F]{1,4}){1,7}))((/([0-9]|[1-9][0-9]|1[01][0-9]|12[0-8])))?$":
        "must be a valid ipv6 address with optional cidr subnet mask from 0 to 128",
    
    r"^(((25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)(\.(?!$)|$)){4}(\/(3[0-2]|[12]?\d))?)$|^(([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|(([0-9a-fA-F]{1,4}:){1,7}:)|(:([0-9a-fA-F]{1,4}:){1,7}))(/(12[0-8]|1[01][0-9]|[1-9]?[0-9]))?$":
        "must be a valid ipv4 or ipv6 address with optional CIDR ",
    
    r"^((25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)){3})(/(3[0-2]|[12]?\d|0))?$|^(::ffff:(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)){3})(/(3[0-2]|[12]?\d|0))?$|^([0-9a-fA-F:]+)(/(12[0-8]|1[01][0-9]|[1-9]?\d))?$":
        "must be a valid ipv4 or ipv6 address with optional CIDR"

}

console = Console()

def load_yaml_file(file_path):
    yaml = YAML()
    with open(file_path, 'r') as f:
        data = yaml.load(f)
        console.print(f"YAML file '{file_path}' loaded successfully")
        return data

def load_json_file(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    print("JSON schema loaded successfully")
    return data

def get_line_number(root, path):
    """
    Walk the absolute_path (`jsonschema` list of keys / indexes) and return the
    1-based line number where the failing element starts in the YAML file.
    Handles:
      • Mapping keys   - uses obj.lc.key(idx)[0]
      • Sequence items - uses seq.lc.item(idx)[0]
    """
    try:
        cur = root
        for p in path:
            # ----- sequence position -----
            if isinstance(cur, CommentedSeq) and isinstance(p, int):
                # Save line of this list item (if available) before descending
                if hasattr(cur.lc, "item") and cur.lc.item(p):
                    line = cur.lc.item(p)[0] + 1  # 0-based → 1-based
                else:
                    line = None
                cur = cur[p]
            # ----- mapping position -----
            elif isinstance(cur, CommentedMap) and isinstance(p, str):
                # Save line of the *key* (not the value) before descending
                if hasattr(cur.lc, "key") and cur.lc.key(p):
                    line = cur.lc.key(p)[0] + 1
                else:
                    line = None
                cur = cur[p]
            else:        # unexpected shape
                return None
        return line
    except Exception:
        return None

def describe_error(error: ValidationError, instance: dict):
    def resolve_path(path, root):
        NAMING_KEYS = ["name", "nodeName", "portName", "vni", "vrf"]
        path_parts = []
        current = root

        for part in path:
            if isinstance(part, int) and isinstance(current, list):
                item = current[part]
                label = next((str(item[k]) for k in NAMING_KEYS if k in item), None)
                if label:
                    path_parts[-1] = f"{path_parts[-1]}[{label}]"
                else:
                    path_parts[-1] = f"{path_parts[-1]}[{part}]"
                current = item
            elif isinstance(current, dict) and part in current:
                path_parts.append(str(part))
                current = current[part]

        return "/".join(path_parts) or "(root)", current

    field_path, error_obj = resolve_path(error.path, instance)
    user_value = error.instance
    line = get_line_number(instance, error.absolute_path)

    # Build rich message
    msg = Text()

    # Add location info
    if line is not None:
        msg.append(f"Line {line}", style="bold green")
    msg.append(", path ", style="white")
    msg.append(f"'{field_path}'", style="yellow")

    if error.validator == "additionalProperties":
        extra = error.message.split("('")[1].split("'")[0]
        offending_line = None

        if hasattr(error_obj, 'lc') and hasattr(error_obj.lc, 'data') and extra in error_obj.lc.data:
            # Try key line number first
            key_line_info = error_obj.lc.key(extra)
            if key_line_info is not None:
                offending_line = key_line_info[0] + 1
            else:
                val_line_info = error_obj.lc.value(extra)
                if val_line_info is not None:
                    offending_line = val_line_info[0] + 1

        line_number_to_report = offending_line if offending_line is not None else line

        msg = Text()
        if line_number_to_report is not None:
            msg.append(f"Line {line_number_to_report}", style="bold green")
        msg.append(", path ", style="white")
        msg.append(f"'{field_path}'", style="yellow")
        msg.append(": extra property ", style="white")
        msg.append(f"'{extra}'", style="cyan")
        msg.append(" is not allowed", style="white")
        return msg
    
    # Custom management port logic
    if "managementPorts" in str(error.path) and error.validator in ("required", "not"):
        seen = set()  # Track which configType/address/gateway pairs we've already handled

        for ip_version in ("ipv4", "ipv6"):
            config_type_field = f"{ip_version}ConfigType"
            address_field = f"{ip_version}Address"
            gateway_field = f"{ip_version}Gateway"

            config_type = error_obj.get(config_type_field)
            has_address = address_field in error_obj
            has_gateway = gateway_field in error_obj

            # Skip if we've already handled this field combo
            if (config_type_field, address_field, gateway_field) in seen:
                continue
            seen.add((config_type_field, address_field, gateway_field))

            if config_type == "CONFIG_TYPE_DHCP" and (has_address or has_gateway):
                msg.append(": ", style="white")
                msg.append(f"When '{config_type_field}' is set to 'DHCP', ", style="white")
                msg.append("you must not provide ", style="white")
                if has_address:
                    msg.append(f"'{address_field}'", style="cyan")
                if has_address and has_gateway:
                    msg.append(" and ", style="white")
                if has_gateway:
                    msg.append(f"'{gateway_field}'", style="cyan")
                msg.append(".", style="white")
                return msg

            if config_type == "CONFIG_TYPE_STATIC" and (not has_address or not has_gateway):
                msg.append(": ", style="white")
                msg.append(f"When '{config_type_field}' is 'STATIC', ", style="white")
                if not has_address and not has_gateway:
                    msg.append(f"both '{address_field}' and '{gateway_field}' are missing", style="cyan")
                elif not has_address:
                    msg.append(f"'{address_field}' is missing", style="cyan")
                elif not has_gateway:
                    msg.append(f"'{gateway_field}' is missing", style="cyan")
                return msg

    # Otherwise show value
    msg.append(", value ", style="white")
    msg.append(repr(user_value), style="cyan")
    msg.append(": ", style="white")

    # Standard explanation fallbacks
    if error.validator == "pattern":
        pattern = error.validator_value
        explanation = REGEX_DESCRIPTIONS.get(pattern, f"must match pattern {pattern}")
        msg.append(explanation, style="white")
    elif error.validator == "type":
        msg.append(f"expected type '{error.validator_value}'", style="white")
    elif error.validator == "enum":
        allowed = ", ".join(map(str, error.validator_value))
        msg.append(f"must be one of: {allowed}", style="white")
    elif error.validator in {"minimum", "maximum"}:
        msg.append(f"value must be {error.validator} {error.validator_value}", style="white")
    elif error.validator in {"minLength", "maxLength"}:
        msg.append(f"string length must be {error.validator} {error.validator_value}", style="white")
    elif error.validator == "required":
        msg.append(error.message, style="white")
    else:
        msg.append(error.message, style="white")

    return msg

def check_for_duplicate_names(instance: Dict[str, Any]) -> List[SimpleNamespace]:
    errors = []

    def make_error(path: List[Any], instance_value: Any, msg: str) -> SimpleNamespace:
        return SimpleNamespace(
            path=path,
            absolute_path=path,
            instance=instance_value,
            message=msg,
            validator="duplicate",
            validator_value=None
        )

    def recurse(obj: Any, path: List[Any]):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, list):
                    seen_names = set()
                    for idx, item in enumerate(value):
                        if isinstance(item, dict):
                            name = item.get("name")
                            if name:
                                if name in seen_names:
                                    error_path = path + [key, idx, "name"]
                                    msg = f"Duplicate name '{name}'"
                                    errors.append(make_error(error_path, name, msg))
                                else:
                                    seen_names.add(name)
                        # Recurse into list item
                        recurse(item, path + [key, idx])
                else:
                    recurse(value, path + [key])
        elif isinstance(obj, list):
            for idx, item in enumerate(obj):
                recurse(item, path + [idx])

    recurse(instance, [])
    return errors

def validate_json(instance, file_path, schema):
    #field_order = get_field_order(schema)
    validator = Draft7Validator(schema)

    # Collect errors
    errors = list(validator.iter_errors(instance))
    dup_errors = check_for_duplicate_names(instance)

    # Apply describe_error to everything for standardized formatting
    all_errors = (
        [describe_error(e, instance) for e in errors] +
        [describe_error(e, instance) for e in dup_errors]
    )   

    # Sort by line number (which is now inside the Text output as part of formatting)
    def extract_line_number(msg):
        try:
            prefix = str(msg).split(",")[0]
            if prefix.startswith("Line "):
                return int(prefix.replace("Line ", ""))
        except:
            pass
        return float('inf')

    sorted_errors = sorted(all_errors, key=extract_line_number)

    if not all_errors:
        console.print(f"{file_path} is valid according to the JSON schema.", style="bold green")
        print("=" * 50)
        return True
    else:
        console.print(f"YAML validation errors found in file '{file_path}':", style="bold red")
        for e in sorted_errors:
            console.print(e)
        print("=" * 50)
        return False

def validate_schema(yaml_path):
    schema_path = get_schema_path()    

    yaml_data = load_yaml_file(yaml_path)
    json_schema = load_json_file(schema_path)

    return validate_json(yaml_data, yaml_path, json_schema)