import requests
import json
import logging
import copy
from pprint import pprint
from entities.attributes import parse_attributes

# Setup logger
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Action stack to support rollback on error.
# Each entry is a tuple: (function_to_call, data_to_pass)
action_stack = []

def _clear_action_stack():
    action_stack.clear()

def _rollback():
    total_length = len(action_stack)
    print(f"Size of action_stack: {total_length}")
    while action_stack:
        func, data, protected = action_stack.pop()
        if protected and protected.active:
            logger.info(f"[ROLLBACK] Handling ROLLBACK ({(total_length - len(action_stack))}/{total_length})... Protected item removed from rollback sequence")
            continue
        response = None
        try:
            if (func is None or hasattr(func, '__name__') == False):
                logger.error(f"[ROLLBACK] Error handling rollback ({(total_length - len(action_stack))}/{total_length}). Invalid rollback function.")
                continue
            logger.info(f"[ROLLBACK] Handling ROLLBACK ({(total_length - len(action_stack))}/{total_length})... calling {func.__name__}")
            pprint(data)
            response = func(data)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"[ROLLBACK] Failed to rollback action {func.__name__}: {e}")
            try:
                error_message = response.json()
            except (json.JSONDecodeError, ValueError):
                error_message = response.text

            logger.error(f"[ROLLBACK] HTTP Error in {func.__name__}: {e}. "
                        f"Status code: {response.status_code}. Response: {error_message}")
            
def _append_to_put_object(curr_obj, put_obj, key):
    for attr in curr_obj:
        if attr not in put_obj[key]:
            put_obj[key][attr] = curr_obj[attr]

def _handle_put(put_func, rollback_func, func_input, key=None, rollback_input=None):
    logger.info(f"[{key.upper()}] [PUT] Making API request for object: {key}...")
    response = None
    put_func_name = getattr(put_func, '__name__', str(put_func))
    try:
        response = put_func(func_input)
        response.raise_for_status()

        # Success -> push to stack
        if (rollback_input is not None):
            action_stack.append((rollback_func, rollback_input, func_input.get("protected")))
        return response

    except requests.exceptions.HTTPError as e:
        try:
            error_message = response.json()
        except (json.JSONDecodeError, ValueError):
            error_message = response.text

        logger.error(f"[{key.upper()}] [PUT HANDLER] HTTP Error in {put_func_name}: {e}. "
                     f"Status code: {response.status_code}. Response: {error_message}")
        _rollback()
        return response
    except requests.exceptions.RequestException as e:
        logger.error(f"[{key.upper()}] [PUT HANDLER] Request failed in {put_func_name}: {e}")
        _rollback()
        return response
    except Exception as e:
        logger.exception(f"[{key.upper()}] [PUT HANDLER] Unexpected error in {put_func_name}: {e}")
        _rollback()
        return response

def _handle_post(post_func, rollback_func, func_input, key=None):
    logger.info(f"[{key.upper()}] [POST] Making API request for object: {key}...")
    response = None
    post_func_name = getattr(post_func, '__name__', str(post_func))
    try:
        response = post_func(func_input)
        response.raise_for_status()

        # ID is known after POST call for a connection or VNI, and is needed in the delete function
        if key is not None and (key == "connection" or key == "vni"):
            try:
                protected = func_input.pop("protected", None) # Pop and re-add later so it doesn't get deep copied, we want the original reference
                func_input = copy.deepcopy(func_input)
                func_input["id"] = response.json().get(f"{key}s")[0].get("id")

                if protected is not None:
                    func_input["protected"] = protected
            except Exception as e:
                logger.error(f"[{key.upper()}] [POST HANDLER] Error accessing ID of connection: {e}")

        # Success -> push to stack
        action_stack.append((rollback_func, func_input, func_input.get("protected")))
        return response

    except requests.exceptions.HTTPError as e:
        try:
            error_message = response.json()
        except (json.JSONDecodeError, ValueError):
            error_message = response.text

        logger.error(f"[{key.upper()}] [POST HANDLER] HTTP Error in {post_func_name}: {e}. "
                     f"Status code: {response.status_code}. Response: {error_message}")
        _rollback()
        return response
    except requests.exceptions.RequestException as e:
        logger.error(f"[{key.upper()}] [POST HANDLER] Request failed in {post_func_name}: {e}")
        _rollback()
        return response
    except Exception as e:
        logger.exception(f"[{key.upper()}] [POST HANDLER] Unexpected error in {post_func_name}: {e}")
        _rollback()
        return response

def handle_get(get_func, post_func, put_func, delete_func, func_input, key, clear_action_stack=False):
    """
    Attempts GET → if not found (404), POST, otherwise PUT.
    Args:
        get_func (func): function call for GET request
        post_func (func): function call for POST request
        put_func (func): function call for PUT request
        delete_func (func): function for DELETE request
        func_input (dict): JSON object for function input
        key (string): identifies the type of object (an attribute)
        clear_action_stack (bool): clears the stack of rollback actions
    Returns: response object
    """
    # Empty stack of rollback functions when starting at the fabric level
    if clear_action_stack:
        _clear_action_stack()
    response = None

    try:
        # Handle post or put directly
        if (get_func is None):
            if (post_func and put_func is None):
                return _handle_post(post_func=post_func, rollback_func=delete_func, func_input=func_input, key=key)
            if (put_func and post_func is None):
                return _handle_put(put_func=put_func, rollback_func=put_func, func_input=func_input, key=key)
            return response
        
        logger.info(f"[{key.upper()}] [GET] Making API request for object: {key}...")
        get_func_name = getattr(get_func, '__name__', str(get_func))

        response = get_func(func_input)
        response.raise_for_status()

        # Extract payload
        payload = None
        try:
            payload = response.json()
        except ValueError:
            payload = response.text
        if (put_func is None): 
            return payload
 
        rollback_input = None
        if key == 'fabric':
            rollback_input = payload
        else:
            rollback_input = copy.deepcopy(func_input)
            obj_pure, _ = parse_attributes(payload, key)
            rollback_input[key] = obj_pure

        _append_to_put_object(rollback_input[key] if key in rollback_input else rollback_input, func_input, key)

        return _handle_put(put_func=put_func, rollback_func=put_func, func_input=func_input, key=key, rollback_input=rollback_input)
        
    except requests.exceptions.HTTPError as http_err:
        if response is not None and response.status_code == 404:
            try:
                err_json = response.json()
                logger.warning(f"[{key.upper()}] [GET HANDLER] Not Found: {err_json.get('message')}")
            except (json.JSONDecodeError, ValueError):
                logger.warning(f"[{key.upper()}] [GET HANDLER] 404 error with no JSON body.")
            if (post_func is None): 
                _rollback()
                return response
            
            return _handle_post(post_func=post_func, rollback_func=delete_func, func_input=func_input, key=key)
        
        else:
            try:
                error_message = response.json()
            except (json.JSONDecodeError, ValueError):
                error_message = response.text if response else "No response object"
            logger.error(f"[{key.upper()}] [GET HANDLER] HTTP error in {get_func_name}: {http_err}. "
                         f"Status code: {response.status_code if response else 'N/A'}. Response: {error_message}")
            _rollback()
            return response

    except requests.exceptions.RequestException as req_err:
        try:
            error_message = response.json()
        except (json.JSONDecodeError, ValueError):
            error_message = response.text if response else "No response object"
        logger.error(f"[{key.upper()}] [GET HANDLER] RequestException in {get_func_name}: {req_err}. "
                     f"Status code: {response.status_code if response else 'N/A'}. Response: {error_message}")
        _rollback()
        return response

    except Exception as e:
        logger.exception(f"[{key.upper()}] [GET HANDLER] Unexpected error in {get_func_name}: {e}")
        _rollback()
        return response
    
def handle_delete(delete_func, data_obj, key):
    """
    Deletes an object directly, not part of the rollback function.

    Args:
        delete_func (func): function for DELETE request
        data_obj (dict): JSON object for function input

    Returns:
        response object if successful, else None
    """
    try:
        logger.info(f"[{key.upper()}] [DELETE] Making API request for object: {key}")
        response = delete_func(data_obj)
        response.raise_for_status()

        return response
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"[{key.upper()}] [DELETE HANDLER] HTTP error occurred while deleting: {http_err}")
    except requests.exceptions.RequestException as req_err:
        logger.error(f"[{key.upper()}] DELETE HANDLER] Request error occurred while deleting: {req_err}")
    except Exception as e:
        logger.error(f"[{key.upper()}] DELETE HANDLER] Unexpected error occurred while deleting: {e}", exc_info=True)
    
    return None

def put_connections(fabric_id, connections, put_func):
    """
    Calls PUT for connections. Separate handler from process_entity since this PUT method sets ALL connections, not just single connection objects.

    Args:
        fabric_id (str): Fabric name
        connections (arr): Array of connection objects
        put_func (func): PUT method for connections
    Returns: response object
    """
    try:
        response = put_func(fabric_id, connections) # Sets ALL connections
        response.raise_for_status()
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"[CONNECTIONS] [SET HANDLER] HTTP error while setting connections for fabric {fabric_id}: {http_err}")
    except requests.exceptions.RequestException as req_err:
        logger.error(f"[CONNECTIONS] [SET HANDLER] Request exception while setting connections for fabric {fabric_id}: {req_err}")
    except Exception as e:
        logger.error(f"[CONNECTIONS] [SET HANDLER] Unexpected error while setting connections for fabric {fabric_id}: {e}", exc_info=True)
    
    return response