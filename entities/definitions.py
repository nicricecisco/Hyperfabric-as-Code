ENTITY_KEYS = [
    "FABRIC",
    "NODE",
    "MGMT_PORT",
    "PORT",
    "CONNECTION",
    "VNI",
    "VRF",
    "STATIC_ROUTE",
    "NEW_OBJECT",
]
ENTITY_PATHS = {
    "FABRIC": ["fabrics"],
    "NODE": ["fabrics", "nodes"],
    "MGMT_PORT": ["fabrics", "nodes", "managementPorts"],
    "PORT": ["fabrics", "nodes", "ports"],
    "CONNECTION": ["fabrics", "connections"],
    "VNI": ["fabrics", "vnis"],
    "VRF": ["fabrics", "vrfs"],
    "STATIC_ROUTE": ["fabrics", "vrfs", "staticRoutes"],
    "NEW_OBJECT": ["fabrics", "newObjects"],
}
