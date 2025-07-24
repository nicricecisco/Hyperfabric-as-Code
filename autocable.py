import sys
import os
import yaml
import logging
from pprint import pprint
from scripts.autocabling import autocabling

# Setup logger
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def handle_yaml_file(input_yaml):
    # Extract just the necessary components (fabric name, nodes, connections)
    with open(input_yaml, "r") as f:
        input_json = yaml.safe_load(f)
    fabrics = input_json.get("fabrics", [])

    if not fabrics:
        logger.warning(f"[AUTOCABLE] No top level 'fabrics' attribute found in {input_yaml}")
        return
    if len(fabrics) > 1:
        logger.warning(f"[AUTOCABLE] Autocabling will only be done for the first fabric in {input_yaml}")
    
    fabric = fabrics[0]
    filtered = {
        "name": fabric.get("name"),
        "nodes": fabric.get("nodes"),
        "connections": fabric.get("connection"),
        "autocabling": fabric.get("autocabling")
    }

    if filtered["name"] is None:
        logger.warning(f"[AUTOCABLE] Fabric in {input_yaml} is missing the 'name' attribute")
        return
    if filtered["nodes"] is None:
        logger.warning(f"[AUTOCABLE] No nodes found in {input_yaml} to autocable")
        return
    
    logger.info(f"[AUTOCABLE] Processing fabric: {filtered['name']}")

    # Remember to validate it against our validator
    
    autocabling_data_obj = {
        "fabric_id": filtered["name"],
        "nodes": filtered["nodes"],
        "connections": filtered["connections"],
        "autocabling_obj": filtered["autocabling"] or {}
    }

    return autocabling(autocabling_data_obj=autocabling_data_obj, pull_nodes_from_yaml=True)

def handle_fabric_name(fabric_name):
    pass

def is_yaml_file(input_str):
    return input_str.endswith((".yaml", ".yml")) and os.path.isfile(input_str)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <yaml_file or fabric_name>")
        sys.exit(1)

    input_arg = sys.argv[1]

    if is_yaml_file(input_arg):
        connections, redundant_connections, connections_to_delete, existing_connections = handle_yaml_file(input_arg)
    else:
        connections = handle_fabric_name(input_arg)

    pprint(connections)
