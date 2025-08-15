from string import Template

template_comment_header = '''
# ------------------------------ {KEY_UPPER} ------------------------------
'''

# # -------------------- STATIC ROUTES --------------------
#             if "staticRoutes" in vrf_other:
#                 for static_route in vrf_other["staticRoutes"]:
#                     static_route_data_obj = {
#                         "fabric_id": FABRIC_ID,
#                         "vrf_id": vrf["name"],
#                     }
#                     static_route_other = _process_entity(static_route, static_route_data_obj, "static_route")