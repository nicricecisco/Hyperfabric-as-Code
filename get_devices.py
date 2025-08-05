import sys
import logging
import requests
import argparse
from ruamel.yaml import YAML
from utils.timestamp import generate_timestamp
from scripts.hyperfabric_api import get_devices

yaml = YAML()
yaml.indent(mapping=2, sequence=4, offset=2) 

# Setup logger
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def fetch_devices():
    try:
        response = get_devices()
        response.raise_for_status()  # raises HTTPError if response.status_code >= 400
        devices = response.json()
        logger.info(f"Successfully retrieved {len(devices.get('devices', []))} devices.")
        return devices, response
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error while retrieving devices: {e}")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error while retrieving devices: {e}")
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout while retrieving devices: {e}")
    except requests.exceptions.RequestException as e:
        logger.error(f"General request error while retrieving devices: {e}")
    except Exception as e:
        logger.exception("Unexpected error while retrieving devices.")

    return None, None  # Return None or raise, depending on your needs

def filter_attributes(devices):
    devices = devices["devices"]
    wanted_attributes = ["deviceId", "serialNumber", "modelName", "name"]
    default_nodeId = "00000000-0000-0000-0000-000000000000"
    # Only return devices whose nodeId is 0000...
    return {
        "devices": [{k: d[k] for k in wanted_attributes if k in d} for d in devices if d.get("nodeId", default_nodeId) == default_nodeId]
    }

def main(only_unbound=False):
    devices, response = fetch_devices()
    output_path = "output/devices.yaml"
    
    if response:
        now = generate_timestamp()
        comment = f"# Generated on {now}"
        if devices:
            if only_unbound:
                devices = filter_attributes(devices)

            with open(output_path, "w") as f:
                f.write(comment + "\n")
                yaml.dump(devices, f)
            logger.info(f"Wrote devices to {output_path}")
        else:
            logger.info("No devices found")
            with open(output_path, "w") as f:
                f.write(comment + "\n")
    else:
        logger.error("Error retrieving devices")

def parse_args():
    parser = argparse.ArgumentParser(description="Get devices")
    parser.add_argument(
        '--unbound',
        action='store_true',
        help='Only output devices that are not bound to nodes'
    )

    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    if args.unbound:
        main(only_unbound=True)
    else:
        main()