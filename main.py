import sys
import argparse
from pprint import pprint
from validate_yaml import validate_files
from program_files.utils.merge_files import combine_files
from program_files.utils.timestamp import generate_timestamp
from program_files.scripts.handle_json_input import handle_json_input

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

def parse_args():
    parser = argparse.ArgumentParser(description="Upload to Hyperfabric")
    parser.add_argument(
        "yaml_files",
        nargs="+",
        help="One or more YAML files to process"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Bypass the validator and force an upload to Hyperfabric"
    )
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    yaml_files = args.yaml_files
    force = args.force

    all_valid_files = validate_files(yaml_files)
    if not all_valid_files and not force:
        sys.exit(1)
        
    json_input = combine_files([file for file in yaml_files])

    results = main(json_input)
    now = generate_timestamp()
    if results.get("status"):
        add_comment(yaml_files, f"Last uploaded ({results['status']}): {now}")