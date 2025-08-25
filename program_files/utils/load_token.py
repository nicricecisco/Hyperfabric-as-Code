import os
from pathlib import Path
from dotenv import dotenv_values, load_dotenv
from program_files.utils.logger import get_logger

# Setup logger
logger = get_logger()

def load_token():
    # Define path to .env
    dotenv_path = Path(__file__).resolve().parents[2] / ".env"

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
