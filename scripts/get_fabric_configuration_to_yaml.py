#WIP


#!/usr/bin/env python3
"""fetch_fabric_config.py

A utility script that fetches fabric configurations using the `hyperfabric_api`
module and converts the resulting JSON payload to YAML using the helper
function defined in `json_to_yaml.py`.

Usage
-----
$ python fetch_fabric_config.py FABRIC_ID_OR_NAME          # writes ./FABRIC_fabric_config.yaml
$ python fetch_fabric_config.py FABRIC_ID_OR_NAME -o ~/configs/    # writes ~/configs/FABRIC_fabric_config.yaml

Requirements
------------
* scripts/hyperfabric_api.py with a public
  `get_fabric_configurations(fabric_id_or_name)` function that returns a
  JSON‑serialisable Python object (dict / list).
* scripts/json_to_yaml.py with a public `json_to_yaml(data: Any) -> str` function that
  returns a YAML‑formatted string.
* schemas/ directory must be importable for hyperfabric_api dependencies.
"""

from __future__ import annotations

import argparse
import sys
import os
from pathlib import Path
from typing import Any

# Ensure project root and scripts/ are importable
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))      # for schemas/
sys.path.insert(0, str(SCRIPT_DIR))        # for hyperfabric_api and json_to_yaml

try:
    from hyperfabric_api import get_fabric_configurations
except ImportError as exc:
    sys.exit(
        "Could not import `hyperfabric_api`. It must be in the scripts/ directory.\n"
        f"Original error: {exc}"
    )

try:
    from json_to_yaml import json_to_yaml
except ImportError as exc:
    sys.exit(
        "Could not import `json_to_yaml`. Make sure it is in the scripts/ directory.\n"
        f"Original error: {exc}"
    )

def fetch_configurations(fabric_id_or_name: str) -> Any:
    """Fetch the fabric configurations from the API.

    Parameters
    ----------
    fabric_id_or_name : str
        The name or ID of the fabric to fetch.

    Returns
    -------
    Any
        The raw data structure returned by `get_fabric_configurations()`.
    """
    try:
        data = get_fabric_configurations(fabric_id_or_name)
        if not data:
            sys.exit(f"No fabric found with ID or name: '{fabric_id_or_name}'")
        return data
    except Exception as err:  # pylint: disable=broad-except
        sys.exit(f"Failed to retrieve configurations: {err}")


def convert_to_yaml(data: Any) -> str:
    """Convert *data* (a JSON‑compatible Python object) to YAML.

    Parameters
    ----------
    data : Any
        The JSON‑compatible Python object to convert.

    Returns
    -------
    str
        A YAML‑formatted string.
    """
    try:
        return json_to_yaml(data)
    except Exception as err:  # pylint: disable=broad-except
        sys.exit(f"Failed to convert JSON to YAML: {err}")


def write_output(yaml_str: str, destination: Path) -> None:
    """Write *yaml_str* to *destination*.

    Parameters
    ----------
    yaml_str : str
        YAML‑formatted string to write.
    destination : Path
        Where to write the file.
    """
    try:
        destination.write_text(yaml_str, encoding="utf-8")
    except Exception as err:  # pylint: disable=broad-except
        sys.exit(f"Failed to write YAML to {destination}: {err}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command‑line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Fetch fabric configurations via hyperfabric_api and output them as YAML."
        )
    )
    parser.add_argument(
        "fabric_id_or_name",
        type=str,
        help="Fabric name or ID to retrieve configurations for."
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Directory to place the resulting YAML file (default: script directory)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:  # pragma: no cover
    """Script entry‑point."""
    args = parse_args(argv)
    raw_data = fetch_configurations(args.fabric_id_or_name)
    yaml_str = convert_to_yaml(raw_data)

    output_dir = args.output if args.output else SCRIPT_DIR

    if not output_dir.exists() or not output_dir.is_dir():
        sys.exit(f"Output path does not exist or is not a directory: {output_dir}")

    output_file = output_dir / f"{args.fabric_id_or_name}_fabric_config.yaml"
    write_output(yaml_str, output_file.resolve())

    print(f"Fabric configuration written to {output_file.resolve()}")


if __name__ == "__main__":
    main()
