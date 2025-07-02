import requests
import json
import logging
from pprint import pprint
from scripts.hyperfabric_api import create_fabric, get_fabric, update_fabric

# Setup logger
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def _handle_put(put_func, func_input):
    logger.info("Handling PUT...")
    response = None
    put_func_name = getattr(put_func, '__name__', str(put_func))
    try:
        response = put_func(func_input)
        response.raise_for_status()
        return response

    except requests.exceptions.HTTPError as e:
        try:
            error_message = response.json()
        except (json.JSONDecodeError, ValueError):
            error_message = response.text

        logger.error(f"[PUT HANDLER] HTTP Error in {put_func_name}: {e}. "
                     f"Status code: {response.status_code}. Response: {error_message}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"[PUT HANDLER] Request failed in {put_func_name}: {e}")
        return None
    except Exception as e:
        logger.exception(f"[PUT HANDLER] Unexpected error in {put_func_name}: {e}")
        return None

def _handle_post(post_func, func_input):
    logger.info("Handling POST...")
    response = None
    post_func_name = getattr(post_func, '__name__', str(post_func))
    try:
        response = post_func(func_input)
        response.raise_for_status()
        return response

    except requests.exceptions.HTTPError as e:
        try:
            error_message = response.json()
        except (json.JSONDecodeError, ValueError):
            error_message = response.text

        logger.error(f"[POST HANDLER] HTTP Error in {post_func_name}: {e}. "
                     f"Status code: {response.status_code}. Response: {error_message}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"[POST HANDLER] Request failed in {post_func_name}: {e}")
        return None
    except Exception as e:
        logger.exception(f"[POST HANDLER] Unexpected error in {post_func_name}: {e}")
        return None

def _handle_get(get_func, post_func, put_func, func_input):
    """
    Attempts GET → if not found (404), POST → if found, PUT.
    Returns: response object or None
    """
    logger.info("Handling GET...")
    response = None
    get_func_name = getattr(get_func, '__name__', str(get_func))

    try:
        response = get_func(func_input)
        response.raise_for_status()
        return _handle_put(put_func, func_input)

    except requests.exceptions.HTTPError as http_err:
        if response is not None and response.status_code == 404:
            try:
                err_json = response.json()
                logger.warning(f"[GET HANDLER] Not Found: {err_json.get('message')}")
            except (json.JSONDecodeError, ValueError):
                logger.warning("[GET HANDLER] 404 error with no JSON body.")
            return _handle_post(post_func, func_input)
        else:
            try:
                error_message = response.json()
            except (json.JSONDecodeError, ValueError):
                error_message = response.text if response else "No response object"
            logger.error(f"[GET HANDLER] HTTP error in {get_func_name}: {http_err}. "
                         f"Status code: {response.status_code if response else 'N/A'}. Response: {error_message}")
            return None

    except requests.exceptions.RequestException as req_err:
        try:
            error_message = response.json()
        except (json.JSONDecodeError, ValueError):
            error_message = response.text if response else "No response object"
        logger.error(f"[GET HANDLER] RequestException in {get_func_name}: {req_err}. "
                     f"Status code: {response.status_code if response else 'N/A'}. Response: {error_message}")
        return None

    except Exception as e:
        logger.exception(f"[GET HANDLER] Unexpected error in {get_func_name}: {e}")
        return None

def handle_json_input(json_input):
    """
    Attempts GET → if not found, POST → if found, PUT.
    Logs and prints final response object.
    """
    response = _handle_get(get_fabric, create_fabric, update_fabric, json_input)
    pprint(response)
