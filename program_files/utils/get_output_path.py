import os

REPO_ROOT = os.path.dirname(os.path.abspath(os.path.join(__file__, "..", ".."))) # This file is nested 2 folders down from root

def get_output_path(file_name):
    output_dir = os.path.join(REPO_ROOT, "output")
    os.makedirs(output_dir, exist_ok=True)  # ensures folder exists

    file_path = os.path.join(output_dir, f"{file_name}.yaml")

    return file_path
