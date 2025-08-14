from string import Template

template_comment_header = '''
# ------------------------------ {KEY_UPPER} ------------------------------
'''

template_args_entry = Template('''
- "${KEY_A_PARENT_ID_SNAKE}" (str): The ID or name of the ${KEY_A_PARENT_SINGULAR}.
''')

template_extract_id = Template('''
${KEY_A_PARENT_ID_CAMEL} = ${KEY_DATA_OBJ}["${KEY_A_PARENT_ID_SNAKE}"]
''')

template_single_portion_of_api_path = Template('''
/${KEY_A_PARENT_PLURAL}/{{${KEY_A_PARENT_ID_CAMEL}}}
''')

template_get_all_call = Template('''
def get_fabric_${KEY_LOWER_SNAKE_PLURAL}(${KEY_DATA_OBJ}):
    """
     Gets a list of ${KEY_CAMEL} for a ${KEY_PARENT_SINGULAR}

     Args:
         ${KEY_DATA_OBJ} (dict): A dictionary containing ${KEY_PARENT_ID_LIST}. Expected keys:
            ${INSERT_PARENT_ARG_LIST}

    Returns:
        dict: JSON response, or None on error.
    """
    params = {key: ${KEY_DATA_OBJ}["${KEY_LOWER_SNAKE_SINGULAR}"][key] for key in ["candidate", "includeMetadata"] if key in ${KEY_DATA_OBJ}.get("${KEY_LOWER_SNAKE_PLURAL}", {})}
    ${INSERT_TEMPLATE_EXTRACT_ID}
    response = _make_get_request(headers, f"{BASE_URL}${KEY_PATH_ROOT_TO_KEY}", params=params)
    return response
''')

template_post_call = '''
def add_fabric_${KEY_LOWER_SNAKE_PLURAL}(${KEY_DATA_OBJ}):
    """
    Creates or updates one or more KEY_CAMEL_SINGULAR objects for a fabric ${KEY_PARENT_SINGULAR} object.

    Args:
        ${KEY_DATA_OBJ} (dict): A dictionary containing ${KEY_PARENT_ID_LIST} and KEY_CAMEL data. Expected keys:
            ${INSERT_PARENT_ARG_LIST}
            - "${KEY_LOWER_SNAKE_PLURAL}" (dict): A dictionary representing a single KEY_CAMEL_SINGULAR object to add.
              
              Note: The function wraps this single KEY_CAMEL_SINGULAR in a list for the API call.

    Returns:
        dict: JSON response, or None on error.
    """
    payload = {"KEY_CAMEL": [${KEY_DATA_OBJ}["${KEY_LOWER_SNAKE_PLURAL}"]]}
    ${INSERT_TEMPLATE_EXTRACT_ID}
    response = _make_post_request(headers,f"{BASE_URL}${KEY_PATH_ROOT_TO_KEY}",payload=payload)
    return response
'''

template_get_call = '''
def get_fabric_KEY_LOWER_SNAKE_SINGULAR(${KEY_DATA_OBJ}):
    """
     Gets information for a single KEY_CAMEL_SINGULAR.

     Args:
         ${KEY_DATA_OBJ} (dict): A dictionary containing ${KEY_PARENT_ID_LIST} and KEY_CAMEL_SINGULAR data. Expected keys:
             ${INSERT_PARENT_ARG_LIST}
             - "${KEY_LOWER_SNAKE_PLURAL}" (dict): A dictionary containing the KEY_CAMEL_SINGULAR's name.
               Expected sub-keys:
                 - "name" (str): The ID or name of the KEY_CAMEL_SINGULAR.

    Returns:
        int: JSON response on success or None on Fail
    """
    params = {key: ${KEY_DATA_OBJ}["${KEY_LOWER_SNAKE_PLURAL}"][key] for key in ["candidate", "includeMetadata"] if key in ${KEY_DATA_OBJ}["${KEY_LOWER_SNAKE_PLURAL}"]}
    ${INSERT_TEMPLATE_EXTRACT_ID}
    KEY_CAMEL_SINGULARId = ${KEY_DATA_OBJ}["${KEY_LOWER_SNAKE_PLURAL}"]["name"]
    response = _make_get_request(headers, f"{BASE_URL}KEY_PATH_ROOT_TO_KEY_FULL", params=params)
    return response
'''

template_put_call = '''
def update_fabric_KEY_LOWER_SNAKE_SINGULAR(${KEY_DATA_OBJ}):
    """
     Updates a specific KEY_CAMEL_SINGULAR.

     Args:
         ${KEY_DATA_OBJ} (dict): A dictionary containing ${KEY_PARENT_ID_LIST}, KEY_CAMEL_SINGULAR ID, and updated KEY_CAMEL_SINGULAR properties. Expected keys:
             ${INSERT_PARENT_ARG_LIST}
             - "${KEY_LOWER_SNAKE_PLURAL}" (dict): A dictionary containing the updated KEY_CAMEL_SINGULAR properties. Must include "name" for KEY_CAMEL_SINGULAR ID.
        
      Returns:
        dict: JSON response, or None on error.
    """
    ${INSERT_TEMPLATE_EXTRACT_ID}
    KEY_CAMEL_SINGULARId = ${KEY_DATA_OBJ}["${KEY_LOWER_SNAKE_PLURAL}"]["name"]
    payload = ${KEY_DATA_OBJ}["${KEY_LOWER_SNAKE_PLURAL}"]
    response = _make_put_request(headers, f"{BASE_URL}KEY_PATH_ROOT_TO_KEY_FULL", payload=payload)
    return response
'''

template_delete_call = '''
def delete_fabric_KEY_LOWER_SNAKE_SINGULAR(${KEY_DATA_OBJ}):
   """
    Deletes a KEY_CAMEL_SINGULAR.

    Args:
         ${KEY_DATA_OBJ} (dict): A dictionary containing ${KEY_PARENT_ID_LIST}, and KEY_CAMEL_SINGULAR ID. Expected keys:
             ${INSERT_PARENT_ARG_LIST}
             - "${KEY_LOWER_SNAKE_PLURAL}" (dict): A dictionary containing the name of the KEY_CAMEL_SINGULAR to delete.

    Returns:
        dict: JSON response
   """
   ${INSERT_TEMPLATE_EXTRACT_ID}
   KEY_CAMEL_SINGULARId = ${KEY_DATA_OBJ}["${KEY_LOWER_SNAKE_PLURAL}"]["name"]
   response = _make_delete_request(headers, f"{BASE_URL}KEY_PATH_ROOT_TO_KEY_FULL")
   return response
'''