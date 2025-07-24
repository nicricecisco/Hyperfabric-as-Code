from scripts.hyperfabric_api import \
    get_fabric, create_fabric, update_fabric, delete_fabric, \
    get_fabric_node, add_fabric_nodes, update_fabric_node, delete_fabric_node, \
    get_management_port, add_management_ports, update_management_port, delete_management_port, \
    get_port, update_port, \
    get_fabric_connections, get_fabric_connection, add_fabric_connections, set_fabric_connections, delete_fabric_connection, \
    get_fabric_vni, add_fabric_vnis, update_fabric_vni, delete_fabric_vni, \
    get_fabric_vrf, add_fabric_vrfs, update_fabric_vrf, delete_fabric_vrf, \
    get_fabric_static_route, add_fabric_static_routes, update_fabric_static_route, delete_fabric_static_route

def _make_func_object(get_func, post_func, put_func, del_func):
    return {
        "get_func": get_func,
        "post_func": post_func,
        "put_func": put_func,
        "del_func": del_func
    }

fabric_func_obj = _make_func_object(get_func=get_fabric, post_func=create_fabric, put_func=update_fabric, del_func=delete_fabric)
node_func_obj = _make_func_object(get_func=get_fabric_node, post_func=add_fabric_nodes, put_func=update_fabric_node, del_func=delete_fabric_node)
mgmt_port_func_obj = _make_func_object(get_func=get_management_port, post_func=add_management_ports, put_func=update_management_port, del_func=delete_management_port)
port_func_obj = _make_func_object(get_func=get_port, post_func=None, put_func=update_port, del_func=None)
connection_func_obj = _make_func_object(get_func=None, post_func=add_fabric_connections, put_func=None, del_func=delete_fabric_connection)
vni_func_obj = _make_func_object(get_func=get_fabric_vni, post_func=add_fabric_vnis, put_func=update_fabric_vni, del_func=delete_fabric_vni)
vrf_func_obj = _make_func_object(get_func=get_fabric_vrf, post_func=add_fabric_vrfs, put_func=update_fabric_vrf, del_func=delete_fabric_vrf)
static_route_func_obj = _make_func_object(get_func=get_fabric_static_route, post_func=add_fabric_static_routes, put_func=update_fabric_static_route, del_func=delete_fabric_static_route)

FUNCTION_OBJECTS = {
    "FABRIC": fabric_func_obj,
    "NODE": node_func_obj,
    "MGMT_PORT": mgmt_port_func_obj,
    "PORT": port_func_obj,
    "CONNECTION": connection_func_obj,
    "VNI": vni_func_obj,
    "VRF": vrf_func_obj,
    "STATIC_ROUTE": static_route_func_obj
}