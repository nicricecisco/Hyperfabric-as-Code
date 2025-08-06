import sys
import os
import yaml
import argparse
from pprint import pprint
from utils.logger import get_logger
from utils.timestamp import generate_timestamp
from scripts.autocabling import autocabling

# Setup logger
logger = get_logger()

class IndentListDumper(yaml.SafeDumper):
    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, indentless=False)
    
def filter_connection_info(connections, include_id=False):
    return [
        {
            **({'id': conn.get('id')} if include_id else {}),
            'local': {k: v for k, v in conn['local'].items() if k != 'nodeId'},
            'remote': {k: v for k, v in conn['remote'].items() if k != 'nodeId'},
            'pluggable': conn.get('pluggable')
        }
        for conn in connections
    ]

# Outputs entire yaml file with autocabled connections and suggested connections to delete
def output_connections(fabric, connection_result, output_delete=False):
    connections, redundant_connections, connections_to_delete, existing_connections = connection_result

    wanted_connections = filter_connection_info(connections + existing_connections)
    unwanted_connections = filter_connection_info(redundant_connections + connections_to_delete, output_delete)

    fabric["connections"] = wanted_connections
    fabric.pop("autocabling", None) # Remove autocabling attribute

    fabric_json = {
        "fabrics": [fabric]
    }

    yaml_fabric = yaml.dump(fabric_json, sort_keys=False, Dumper=IndentListDumper, default_flow_style=False)

    output_path = "output/autocable_output.yaml"
    logger.info(f"Writing output to '{output_path}'")

    now = generate_timestamp()
    comment = f"# Generated on {now}"
    try:
        with open(output_path, "w") as f:
            f.write(comment + "\n")
            f.write(yaml_fabric)

        logger.info(f"[COMPLETE] Output written successfully to {output_path}")
    except (OSError, IOError) as e:
        logger.error(f"Failed to write output to '{output_path}': {e}")
        logger.info(f"Writing output to terminal")
        print(yaml_fabric)

    if len(unwanted_connections) > 0:
        if output_delete:
            unwanted_connections = {
                "fabrics": [
                    {
                        "name": fabric.get("name"),
                        "delete": {
                            "connections": unwanted_connections
                        }
                    }
                ]
            }

        yaml_unwanted = yaml.dump(unwanted_connections, sort_keys=False, Dumper=IndentListDumper, default_flow_style=False)

        removed_output_path = "output/removed_connections.yaml"
        logger.info(f"Writing removed connections to '{removed_output_path}' ")

        try:
            with open(removed_output_path, "w") as f:
                f.write(comment + "\n")
                f.write(yaml_unwanted)

            logger.info(f"[COMPLETE] Removed connections written successfully to {removed_output_path}")
        except (OSError, IOError) as e:
            logger.error(f"Failed to write removed connections to '{removed_output_path}': {e}")
            logger.info(f"Writing output to terminal")
            print(yaml_unwanted)
    else:
        print("No connections removed")
    
    # Add instructions on what to do? To send autocable_output.yaml (and possible also removed_connections.yaml) to main.py

def handle_yaml_file(input_yaml, pluggable):
    # REJECT if the fabric exists
    with open(input_yaml, "r") as f:
        input_json = yaml.safe_load(f)
    fabrics = input_json.get("fabrics", [])

    if not fabrics:
        logger.error(f"[AUTOCABLE] No top level 'fabrics' attribute found in {input_yaml}")
        return
    if len(fabrics) > 1:
        logger.warning(f"[AUTOCABLE] Autocabling will only be done for the first fabric in {input_yaml}")
    
    fabric = fabrics[0]
    filtered = { # Extract just the necessary components (fabric name, nodes, connections, autocabling)
        "name": fabric.get("name"),
        "nodes": fabric.get("nodes"),
        "connections": fabric.get("connections"),
        "autocabling": fabric.get("autocabling")
    }

    if pluggable:
        filtered["autocabling"] = {
            "pluggable": pluggable
        }

    if filtered["name"] is None:
        logger.error(f"[AUTOCABLE] Fabric in {input_yaml} is missing the 'name' attribute")
        return
    if filtered["nodes"] is None:
        logger.error(f"[AUTOCABLE] No nodes found in {input_yaml} to autocable")
        return
    
    logger.info(f"[AUTOCABLE] Processing fabric: {filtered['name']}")

    # REMEMBER TO VALIDATE IT AGAINST OUR VALIDATOR!!!! DON'T FORGET THAT STEP! I AM WRITING A LONG COMMENT IN ALL CAPS SO IT HOPEFULLY CATCHES YOUR ATTENTION SO YOU DON'T FORGET IT!!! HERE ARE SOME MORE EXCLAMATION MARKS!!!!!!!!!!
    
    autocabling_data_obj = {
        "fabric_id": filtered["name"],
        "nodes": filtered["nodes"],
        "connections": filtered["connections"],
        "autocabling_obj": filtered["autocabling"] or {}
    }

    connection_result = autocabling(autocabling_data_obj=autocabling_data_obj, pull_nodes_from_yaml=True)
    if connection_result is None:
        logger.error("Autocabling failed")
        return
    
    output_connections(fabric, connection_result)

def handle_fabric_name(fabric_name, pluggable):
    # STILL DOESN'T WORK if you are fixing an existing fabric (does not actually delete the connections that should be deleted)
    # I think I'll have to implement some delete functionality of those connections, because I don't see any other way
    autocabling_data_obj = {
        "fabric_id": fabric_name,
        "autocabling_obj": {}
    }

    if pluggable:
        autocabling_data_obj["autocabling_obj"]["pluggable"] = pluggable

    connection_result = autocabling(autocabling_data_obj=autocabling_data_obj)
    if connection_result is None:
        logger.error("Autocabling failed")
        return

    fabric = {
        "name": fabric_name
    }
    output_connections(fabric, connection_result, output_delete=True)

def is_yaml_file(input_str):
    return input_str.endswith((".yaml", ".yml")) and os.path.isfile(input_str)

def parse_args():
    parser = argparse.ArgumentParser(description="Autocabling pipeline")
    parser.add_argument("input", help="Path to the input YAML file")
    parser.add_argument("--pluggable", help="Optional name of cable to assign to all connections")

    return parser.parse_args()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <yaml_file or fabric_name>")
        sys.exit(1)

    args = parse_args()
    input_arg = args.input
    pluggable = args.pluggable

    if is_yaml_file(input_arg):
        handle_yaml_file(input_arg, pluggable)
    else:
        handle_fabric_name(input_arg, pluggable)