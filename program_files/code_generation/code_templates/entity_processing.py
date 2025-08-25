from string import Template

template_comment_header_main = '''
# -------------------- {KEY_UPPER} --------------------'''

template_parent_id_entry = Template('''
"${A_PARENT_ID}": ${A_PARENT_KEY_SNAKE}["name"],
''')

template_entity_processing_standard = Template('''
if "${KEY_NORMAL}" in ${PARENT_OTHER}:
    for ${KEY_LOWER_SNAKE_SINGULAR} in ${PARENT_OTHER}["${KEY_NORMAL}"]:
        ${KEY_DATA_OBJ} = {
            "fabric_id": FABRIC_ID,
            ${PARENT_ID_LIST}
        }
        ${KEY_OTHER} = _process_entity(${KEY_LOWER_SNAKE_SINGULAR}, ${KEY_DATA_OBJ}, "${KEY_LOWER_SNAKE_SINGULAR}")
''')

template_entity_processing_fabric_child = Template('''
if "${KEY_NORMAL}" in fabric_other:
    for i, ${KEY_LOWER_SNAKE_SINGULAR} in enumerate(fabric_other["${KEY_NORMAL}"]):
        ${KEY_DATA_OBJ} = {
            "fabric_id": FABRIC_ID,
        }
        ${KEY_OTHER} = _process_entity(${KEY_LOWER_SNAKE_SINGULAR}, ${KEY_DATA_OBJ}, "${KEY_LOWER_SNAKE_SINGULAR}", i == 0) # Reset action stack if first ${KEY_LOWER_SNAKE_SINGULAR}
        
        _reset_latest_protected_key() # Reset at the end of processing a ${KEY_LOWER_SNAKE_SINGULAR}
''')

# if "nodes" in fabric_other:
#         for i, node in enumerate(fabric_other["nodes"]):
#             node_data_obj = {
#                 "fabric_id": FABRIC_ID
#             }
#             node_other = _process_entity(node, node_data_obj, "node", i == 0) # Reset action stack if first node

# # -------------------- STATIC ROUTES --------------------
#             if "staticRoutes" in vrf_other:
#                 for static_route in vrf_other["staticRoutes"]:
#                     static_route_data_obj = {
#                         "fabric_id": FABRIC_ID,
#                         "vrf_id": vrf["name"],
#                     }
#                     static_route_other = _process_entity(static_route, static_route_data_obj, "static_route")