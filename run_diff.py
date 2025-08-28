import sys
import yaml
import argparse
from pprint import pprint
from get_fabric_config import main as get_fabric_config
from program_files.utils.logger import get_logger
from program_files.utils.merge_files import combine_files
from program_files.utils.timestamp import generate_timestamp
from program_files.utils.get_output_path import get_output_path

logger = get_logger()

def compare_dicts(new, old, path="fabric"):
    """
    Recursively compare two dictionary-like objects.
    Returns a list of differences in a human-readable format.
    """
    diffs = []

    # Keys present in new but not old (added)
    for k in new.keys() - old.keys():
        diffs.append(("added", f"{path}['{k}']", None, None))

    # Keys present in old but not new (removed)
    for k in old.keys() - new.keys():
        diffs.append(("missing", f"{path}['{k}']", None, None))

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
            # diffs.append(f"Value of {new_path} changed from {old_val!r} to {new_val!r}")
            diffs.append(("modified", new_path, old_val, new_val))

    return diffs


def compare_lists(new_list, old_list, path):
    """
    Compare two lists. If they hold dicts, use key-matching.
    If they hold primitive values, compare by set difference.
    """
    diffs = []

    # Case 1: lists of primitives (str, int, etc.)
    if all(not isinstance(item, dict) for item in new_list + old_list):
        added = set(new_list) - set(old_list)
        removed = set(old_list) - set(new_list)

        for val in added:
            diffs.append(("added", path, None, val))
        for val in removed:
            diffs.append(("missing", path, val, None))
        return diffs

    # Case 2: lists with dicts (your existing keyed logic)
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
                        continue
        return key_map

    new_map, old_map = build_key_map(new_list), build_key_map(old_list)

    for key in new_map:
        if key in old_map:
            diffs.extend(compare_dicts(new_map[key], old_map[key], f"{path}[{key}]"))
        else:
            diffs.append(("added", f"{path}[{key}]", None, None))

    for key in old_map:
        if key not in new_map:
            diffs.append(("missing", f"{path}[{key}]", None, None))

    # Handle un-keyed dicts or other values by index
    new_unnamed = [item for item in new_list if not (isinstance(item, dict) and 
                                                     ("name" in item or ("local" in item and "remote" in item)))]
    old_unnamed = [item for item in old_list if not (isinstance(item, dict) and 
                                                     ("name" in item or ("local" in item and "remote" in item)))]

    for i, (n, o) in enumerate(zip(new_unnamed, old_unnamed)):
        new_item_path = f"{path}[{i}]"
        if isinstance(n, dict) and isinstance(o, dict):
            diffs.extend(compare_dicts(n, o, new_item_path))
        elif n != o:
            diffs.append(("modified", new_item_path, o, n))

    if len(new_unnamed) > len(old_unnamed):
        for item in new_unnamed[len(old_unnamed):]:
            diffs.append(("added", path, None, item))
    elif len(old_unnamed) > len(new_unnamed):
        for item in old_unnamed[len(new_unnamed):]:
            diffs.append(("missing", path, item, None))

    return diffs


def format_diffs(diffs):
    added = []
    missing = []
    modified = []

    for diff in diffs:
        if isinstance(diff, tuple):
            kind, path, old_val, new_val = diff
            if kind == "added":
                if new_val is not None:
                    added.append(f"{path}: {new_val!r}")
                else:
                    added.append(path)
            elif kind == "missing":
                if old_val is not None:
                    missing.append(f"{path}: {old_val!r}")
                else:
                    missing.append(path)
            elif kind == "modified":
                modified.append(f"{path} changed from {old_val!r} to {new_val!r}")
        else:
            # fallback for legacy string diffs
            modified.append(diff)

    lines = []
    if added:
        lines.append("Added:")
        for a in added:
            lines.append(f"  {a}")
    if modified:
        lines.append("\nModifications:")
        for m in modified:
            lines.append(f"  {m}")
    if missing:
        lines.append("\nMissing:")
        for m in missing:
            lines.append(f"  {m}")
    
    return "\n".join(lines)


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
    output_text = format_diffs(diffs)

    with open(output_file, "w") as f:
        f.write(comment + "\n")
        f.write(output_text + "\n")

def merge_fabrics(infra, tenant):
    fabrics_by_name = {}

    for fabric in infra.get("fabrics", []):
        fabrics_by_name[fabric["name"]] = fabric

    for fabric in tenant.get("fabrics", []):
        name = fabric["name"]
        if name in fabrics_by_name:
            # Merge tenant fabric into infra fabric
            # (shallow merge: tenant keys overwrite infra keys)
            fabrics_by_name[name].update(fabric)
        else:
            fabrics_by_name[name] = fabric

    return {"fabrics": list(fabrics_by_name.values())}

def parse_args():
    parser = argparse.ArgumentParser(description="Generate diff between YAML files and Cloud Controller blueprint")
    parser.add_argument(
        "yaml_files",
        nargs="+",
        help="One or more YAML files to process"
    )
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    yaml_files = args.yaml_files

    combined_files = combine_files([file for file in yaml_files])
    for fabric in combined_files["fabrics"]:
        fabric_name = fabric["name"]
        infra, tenant = get_fabric_config(fabric_name)
        existing_data = merge_fabrics(infra, tenant)
        main(fabric, existing_data["fabrics"][0])