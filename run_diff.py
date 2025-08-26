import sys
import yaml
from pprint import pprint
from get_fabric_config import main as get_fabric_config
from program_files.utils.logger import get_logger
from program_files.utils.timestamp import generate_timestamp
from program_files.utils.get_output_path import get_output_path

logger = get_logger()

def compare_dicts(new, old, path="root"):
    """
    Recursively compare two dictionary-like objects.
    Returns a list of differences in a human-readable format.
    """
    diffs = []

    # Keys present in new but not old (added)
    for k in new.keys() - old.keys():
        diffs.append(f"Item {path}['{k}'] added: {new[k]!r}")

    # Keys present in old but not new (removed)
    for k in old.keys() - new.keys():
        diffs.append(f"Item {path}['{k}'] removed: {old[k]!r}")

    # Keys present in both (check values)
    for k in new.keys() & old.keys():
        new_val, old_val = new[k], old[k]
        new_path = f"{path}['{k}']"

        if new_val in ["autocabling", "delete", "bind"]:
            continue

        if isinstance(new_val, dict) and isinstance(old_val, dict):
            diffs.extend(compare_dicts(new_val, old_val, new_path))

        elif isinstance(new_val, list) and isinstance(old_val, list):
            diffs.extend(compare_lists(new_val, old_val, new_path))

        elif new_val != old_val:
            diffs.append(f"Value of {new_path} changed from {old_val!r} to {new_val!r}")

    return diffs


def compare_lists(new_list, old_list, path):
    """
    Compare two lists, intelligently matching dicts by 'name' or by 
    'local'+'remote' nodeName and portName.
    """
    diffs = []

    def build_key_map(lst):
        key_map = {}
        for item in lst:
            if isinstance(item, dict):
                if "name" in item:
                    key_map[item["name"]] = item
                elif "local" in item and "remote" in item:
                    try:
                        local_node = item["local"]["nodeName"]
                        local_port = item["local"]["portName"]
                        remote_node = item["remote"]["nodeName"]
                        remote_port = item["remote"]["portName"]
                        key_map[f"local={local_node}:{local_port}|remote={remote_node}:{remote_port}"] = item
                    except KeyError:
                        # fallback: skip keying
                        continue
        return key_map

    new_map, old_map = build_key_map(new_list), build_key_map(old_list)

    # Compare keyed items
    for key in new_map:
        if key in old_map:
            diffs.extend(compare_dicts(new_map[key], old_map[key], f"{path}[{key}]"))
        else:
            diffs.append(f"Item {path}[{key}] added: {new_map[key]!r}")

    for key in old_map:
        if key not in new_map:
            diffs.append(f"Item {path}[{key}] removed: {old_map[key]!r}")

    # Compare non-keyed items by position
    new_unnamed = [item for item in new_list if not (isinstance(item, dict) and 
                                                     ("name" in item or ("local" in item and "remote" in item)))]
    old_unnamed = [item for item in old_list if not (isinstance(item, dict) and 
                                                     ("name" in item or ("local" in item and "remote" in item)))]

    for i, (n, o) in enumerate(zip(new_unnamed, old_unnamed)):
        new_item_path = f"{path}[{i}]"
        if isinstance(n, dict) and isinstance(o, dict):
            diffs.extend(compare_dicts(n, o, new_item_path))
        elif n != o:
            diffs.append(f"Value of {new_item_path} changed from {o!r} to {n!r}")

    # Remaining unmatched unnamed items
    if len(new_unnamed) > len(old_unnamed):
        for i, item in enumerate(new_unnamed[len(old_unnamed):], start=len(old_unnamed)):
            diffs.append(f"Item {path}[{i}] added: {item!r}")
    elif len(old_unnamed) > len(new_unnamed):
        for i, item in enumerate(old_unnamed[len(new_unnamed):], start=len(new_unnamed)):
            diffs.append(f"Item {path}[{i}] removed: {item!r}")

    return diffs

def main(new_data, existing_data):
    if new_data is None:
        logger.error("No new data to compare with existing data")
        return
    if existing_data is None:
        logger.error("No existing data to compare with new data")
        return
    
    file_name = f"{new_data.get('name', 'file')}_diff"
    output_file = f"{get_output_path(file_name)[:-4]}txt"  # get_output_path is meant for yaml output, but we want to output txt

    diffs = compare_dicts(new_data, existing_data)
    now = generate_timestamp()
    comment = f"(Generated on {now})"
    with open(output_file, "w") as f:
        f.write(comment + "\n")
        for line in diffs:
            f.write(line + "\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <yaml_file1> [yaml_file2]")
        sys.exit(1)

    yaml_file = sys.argv[1]
    second_input = sys.argv[2] if len(sys.argv) > 2 else None

    with open(yaml_file, "r") as f:
        new_data = yaml.safe_load(f)

    # If a fabric name is passed, run get_fabric_config to obtain the yaml file
    if second_input is None:
        fabric_name = None
        try:
            fabric_name = new_data["fabrics"][0]["name"]
        except Exception as e:
            logger.error(f"Cannot obtain fabric name from yaml file: {yaml_file}")
            sys.exit(1)

        infra, tenant = get_fabric_config(fabric_name)
        existing_data = {
            "fabrics": infra["fabrics"] + tenant["fabrics"]
        }
    else:
        with open(second_input, "r") as f:
            existing_data = yaml.safe_load(f)

    try:
        if new_data["fabrics"][0]["name"] != existing_data["fabrics"][0]["name"]:
            logger.warning(f"Comparing fabric {new_data['fabrics'][0]['name']} to fabric {existing_data['fabrics'][0]['name']}...")
    except Exception as e:
        logger.error(f"Error obtaining names of fabrics")
        sys.exit(1)

    main(new_data["fabrics"][0], existing_data["fabrics"][0])