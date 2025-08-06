import yaml
import sys
from pprint import pprint
from copy import deepcopy
from validate_yaml import validate_files
from utils.timestamp import generate_timestamp
from scripts.handle_json_input import handle_json_input
from scripts.submission_validator_nick import validate_schema

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

def main(json_input):
    results = handle_json_input(json_input)
    pprint(results)
    return results

def add_comment(yaml_files, message):
    comment = f"# {message}\n"
    for file in yaml_files:
        with open(file, "r") as f:
            lines = f.readlines()

        # Separate existing top comment block
        generated_comment = None
        existing_comments = []
        rest_of_file = []
        comment_block_ended = False

        for line in lines:
            if not comment_block_ended and line.lstrip().startswith("#"):
                if line.lstrip().startswith("# Generated on"):
                    generated_comment = line
                elif not line.lstrip().startswith("# Last uploaded"):
                    existing_comments.append(line)
            else:
                comment_block_ended = True
                rest_of_file.append(line)
        
        if generated_comment:
            comments = [generated_comment] + [comment] + existing_comments
        else:
            comments = [comment] + existing_comments
        updated_lines = comments + rest_of_file

        with open(file, "w") as f:
            f.writelines(updated_lines)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <yaml_file1> [yaml_file2 ...]")
        sys.exit(1)
    
    yaml_files = sys.argv[1:]

    all_valid_files = validate_files(yaml_files)
    # if not all_valid_files:
    #     sys.exit(1)
        
    json_input = combine_files([file for file in yaml_files])

    results = main(json_input)
    now = generate_timestamp()
    if results.get("status"):
        add_comment(yaml_files, f"Last uploaded ({results['status']}): {now}")