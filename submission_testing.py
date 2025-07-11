import yaml
import json
import sys
from jsonschema import validate, ValidationError

def load_yaml_file(file_path):
    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)
        print("✅ YAML file loaded successfully.")
        return data

def load_json_file(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
        print("✅ JSON schema loaded successfully.")
        return data

def write_json(data, output_path):
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"✅ JSON written to {output_path}")

def validate_json(instance, schema):
    try:
        validate(instance=instance, schema=schema)
        print("✅ YAML is valid according to the JSON schema.")
    except ValidationError as e:
        print("❌ Validation error:", e.message)
        sys.exit(1)

def main():
    if len(sys.argv) != 4:
        print("Usage: python validate_yaml.py input.yaml schema.json output.json")
        sys.exit(1)

    yaml_path = sys.argv[1]
    schema_path = sys.argv[2]
    json_output_path = sys.argv[3]

    # Load and convert
    yaml_data = load_yaml_file(yaml_path)
    json_schema = load_json_file(schema_path)
    write_json(yaml_data, json_output_path)

    # Validate
    validate_json(yaml_data, json_schema)
    print(f"🎉 Converted {yaml_path} to {json_output_path} and validated against {schema_path}.")

if __name__ == "__main__":
    main()
