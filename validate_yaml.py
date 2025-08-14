import sys
from scripts.validate_submission import validate_schema

def validate_files(yaml_files):
    all_valid = True
    for file in yaml_files:
        is_valid_file = validate_schema(file)
        if not is_valid_file:
            all_valid = False
            
    return all_valid

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <yaml_file1> [yaml_file2 ...]")
        sys.exit(1)
    
    validate_files(sys.argv[1:])