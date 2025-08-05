import os
import logging
from pathlib import Path
from dotenv import dotenv_values, load_dotenv

# Setup logger
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def load_token():
    # Define path to .env
    dotenv_path = Path(__file__).resolve().parents[1] / ".env"

    # Read the token from the .env file (without setting it)
    env_file_values = dotenv_values(dotenv_path) if dotenv_path.exists() else {}
    file_token = env_file_values.get("HYPERFABRIC_TOKEN")

    # Read the currently set environment token
    env_token = os.environ.get("HYPERFABRIC_TOKEN")

    # Compare and log only if different
    if file_token and env_token and file_token != env_token:
        logger.warning("HYPERFABRIC_TOKEN in environment is being overridden by .env file.")

    # Actually load .env file, overriding only if needed
    if dotenv_path.exists():
        load_dotenv(dotenv_path, override=True)

    # Now return the token (re-read from updated environment)
    token = os.environ.get("HYPERFABRIC_TOKEN")
    if not token:
        raise RuntimeError("HYPERFABRIC_TOKEN not found in .env file or environment variables")

    return token

# try:
#     TOKEN = os.environ['HYPERFABRIC_TOKEN']
# except KeyError:
#     # Load .env file located in the same directory as this file
#     dotenv_path = Path(__file__).parent / '.env'
#     load_dotenv(dotenv_path)

#     TOKEN = os.environ.get('HYPERFABRIC_TOKEN')
#     if not TOKEN:
#         raise RuntimeError("HYPERFABRIC_TOKEN not found in environment or .env file")