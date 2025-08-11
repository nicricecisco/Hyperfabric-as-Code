import re

def camel_to_screaming_snake(key, make_singular=False):
    # Insert space before each capital letter
    spaced = re.sub(r'(?<!^)(?=[A-Z])', ' ', key)
    # Convert to screaming snake case
    screaming_snake = spaced.replace(' ', '_').upper()
    # Management ports is a special case
    if screaming_snake == "MANAGEMENT_PORTS":
        screaming_snake = "MGMT_PORTS"

    # Remove last character to make word singular
    if make_singular:
        screaming_snake = screaming_snake[:-1]
    return screaming_snake

def find_key_path(data, target_key, path=None):
    """Recursively search for the path to the target_key in a nested dict/list."""
    if path is None:
        path = []

    if isinstance(data, dict):
        for k, v in data.items():
            if k == target_key:
                return path + [k]
            result = find_key_path(v, target_key, path + [k])
            if result:
                return result
    elif isinstance(data, list):
        for i, item in enumerate(data):
            result = find_key_path(item, target_key, path + [i])
            if result:
                return result
    return None


def get_nested(data, path):
    """Navigate to a nested object given a path list."""
    current = data
    for key in path:
        current = current[key]
    return current
