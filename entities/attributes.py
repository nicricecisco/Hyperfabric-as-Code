def parse_attributes(obj, input_key):
    attributes = ATTRIBUTES[f"{input_key.upper()}"]
    pure = {key: obj[key] for key in obj if key in attributes}
    other = {key: obj[key] for key in obj if key not in attributes}

    return pure, other

FABRIC_ATTRIBUTES = [
    "name",
    "address",
    "city",
    "country",
    "description",
    "location",
    "topology",
    "labels",
    "annotations"
]

NODE_ATTRIBUTES = [
    "name",
    "roles",
    "modelName",
    "location",
    "description",
    "serialNumber",
    "labels",
    "psuAirflows",
    "enabled",
    "protected"
]

MGMT_PORT_ATTRIBUTES = [
    "name",
    "description",
    "configOrigin",
    "connectedState",
    "ipv4ConfigType",
    "ipv4Address",
    "ipv4Gateway",
    "ipv6ConfigType",
    "ipv6Address",
    "ipv6Gateway",
    "dnsAddresses",
    "proxyAddress",
    "proxyPassword",
    "proxyUsername",
    "enabled",
    "setProxyPassword",
    "cloudUrls",
    "noProxy"
]

PORT_ATTRIBUTES = [
    "name",
    "description",
    "mtu",
    "fec",
    "pluggable",
    "speed",
    "enabled",
    "roles",
    "linkDown",
    "vrfId",
    "ipv4Address",
    "ipv6Address",
    "annotations"
]

CONNECTION_ATTRIBUTES = [
    "description",
    "osType",
    "pluggable",
    "local",
    "remote",
    "protected"
]

VNI_ATTRIBUTES = [
     "name",
     "description",
     "vni",
     "mtu",
     "labels",
     "enabled",
     "svis",
     "annotations",
     "protected"
]

VRF_ATTRIBUTES = [
     "name",
     "description",
     "enabled",
     "asn",
     "vni",
     "labels",
     "annotations",
     "protected"
]

STATIC_ROUTE_ATTRIBUTES = [
     "name",
     "description",
     "enabled",
     "labels",
     "annotations",
     "routes"
]

ATTRIBUTES = {
    "FABRIC": FABRIC_ATTRIBUTES,
    "NODE": NODE_ATTRIBUTES,
    "MGMT_PORT": MGMT_PORT_ATTRIBUTES,
    "PORT": PORT_ATTRIBUTES,
    "CONNECTION": CONNECTION_ATTRIBUTES,
    "VNI": VNI_ATTRIBUTES,
    "VRF": VRF_ATTRIBUTES,
    "STATIC_ROUTE": STATIC_ROUTE_ATTRIBUTES
}
