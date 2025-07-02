import yaml
import json

def yaml_to_json(yaml_input):
    yaml_data = yaml.safe_load(yaml_input)
    return json.dumps(yaml_data, indent=2)