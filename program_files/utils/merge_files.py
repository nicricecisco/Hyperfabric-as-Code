import yaml
from copy import deepcopy

def merge_fabric_dicts(f1, f2):
    merged = deepcopy(f1)

    for key, value in f2.items():
        if key not in merged:
            merged[key] = value
        elif isinstance(value, list) and isinstance(merged[key], list):
            merged[key].extend(value)
        elif isinstance(value, dict) and isinstance(merged[key], dict):
            merged[key].update(value)
        else:
            # For scalar values, override (last one wins)
            merged[key] = value

    return merged

def combine_files(file_paths):
    fabric_map = {}  # Keyed by fabric name

    for path in file_paths:
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
            if not data or 'fabrics' not in data:
                continue

            for fabric in data['fabrics']:
                name = fabric.get('name')
                if not name:
                    continue  # Skip unnamed fabrics

                if name in fabric_map:
                    fabric_map[name] = merge_fabric_dicts(fabric_map[name], fabric)
                else:
                    fabric_map[name] = deepcopy(fabric)

    return {'fabrics': list(fabric_map.values())}