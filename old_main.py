import json
import yaml
from pprint import pprint

from scripts.hyperfabric_api import get_fabrics, create_fabric
from scripts.json_to_yaml import json_to_yaml
from scripts.yaml_to_json import yaml_to_json

if __name__ == "__main__":
    fabrics = get_fabrics()
    
    # keys_to_include = [
    #     'name', 'description', 'address', 'city', 'country', 'location', 'labels', 'topology'
    # ]

    yaml_output = json_to_yaml(fabrics)
    
    with open("output/output.yaml", "w") as f:
        f.write(yaml_output)
    f.close()

    json_output = yaml_to_json(yaml_output)

    with open("output/output.json", "w") as f:
        f.write(json_output)
    f.close()

    input = None
    with open("input.yaml", "r") as f:
        input = yaml.safe_load(f)
        pprint(input)

        with open("output/output.json", "w") as g:
            json.dump(input, g, indent=4)
        g.close()
    f.close()

    create_output = create_fabric(input)