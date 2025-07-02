import json
import yaml
import sys
from pprint import pprint
from scripts.handle_json_input import handle_json_input

def main(json_input):
    handle_json_input(json_input)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <yaml_file>")
        sys.exit(1)

    yaml_file = sys.argv[1]

    with open(yaml_file, "r") as f:
        json_input = yaml.safe_load(f)
        # pprint(json_input)
    main(json_input)