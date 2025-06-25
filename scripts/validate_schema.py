def _validate_type(value, expected_type):
    type_map = { # Add more types here like integer and float as needed
        "string": str,
        "dict": dict,
        "list": list
    }
    return isinstance(value, type_map.get(expected_type, object))


def validate_against_schema(data, schema, context=""):
    errors = []
    prefix = f"{context}." if context != "" else ""

    for field, rules in schema.items():
        required = rules.get("required", False)
        if required and field not in data:
            errors.append(f"{prefix}{field} is required")
            continue

        if field not in data:
            continue  # Skip validation for missing optional fields

        value = data[field]
        expected_type = rules["type"]
        if not _validate_type(value, expected_type):
            errors.append(f"{prefix}{field} should be of type '{expected_type}'")
            continue

        # Handle nested schema for list or dict
        if expected_type == "list":
            item_schema = rules.get("schema")
            if item_schema:
                for i, item in enumerate(value):
                    if item_schema["type"] == "dict":
                        sub_errors = validate_against_schema(item, item_schema["schema"], f"{prefix}{field}[{i}]")
                        errors.extend(sub_errors)
                    elif not _validate_type(item, item_schema["type"]):
                        errors.append(f"{prefix}{field}[{i}] should be of type '{item_schema['type']}'")
        elif expected_type == "dict":
            sub_schema = rules.get("schema")
            if sub_schema:
                sub_errors = validate_against_schema(value, sub_schema, f"{prefix}{field}")
                errors.extend(sub_errors)

        # Handle allowed values
        if "allowed" in rules and value not in rules["allowed"]:
            errors.append(f"{prefix}{field} has invalid value '{value}'. Allowed: {rules['allowed']}")

    return errors