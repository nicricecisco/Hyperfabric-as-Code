import sys
import os
import yaml
import json
from copy import deepcopy
from pprint import pprint

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts.handle_json_input import handle_json_input
from scripts.hyperfabric_api import delete_fabric

RUN_CREATION_TESTS = True

# Clear the files
for path in ["tests/tests_result.txt", "tests/tests_result_details.txt"]:
    with open(path, "w") as f:
        f.truncate()

def _run_test(name, input):
    result = handle_json_input(input)

    with open("tests/tests_result.txt", "a") as f:
        f.write(f"TEST: {name}: {result['status'].upper()}\n")

    with open("tests/tests_result_details.txt", "a") as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    
    delete_fabric({"name": input["fabrics"][0]["name"]})

basic_yaml_template = """
fabrics:
  - name: python-tests
    nodes:
      - name: Leaf01
        modelName: HF6100-32D
        roles:
          - LEAF
        managementPorts: []
        ports: []
      - name: Spine01
        description: Spine Switch 01
        modelName: HF6100-32D
        roles: 
          - SPINE
    connections: []
    vnis: []
    vrfs:
      - name: VRF01
        enabled: true
        staticRoutes: []
"""
basic_yaml_data = yaml.safe_load(basic_yaml_template)

def _run_creation_tests():
    # # ----------- FABRIC -----------
    # fabric_yaml = """
    # fabrics:
    #   - name: python-tests
    #     description: I am updated from python
    #     location: CA-95134
    #     address: 300 East Tasman Drive
    #     city: Milpitas
    #     country: US
    #     topology: SPINE_LEAF
    #     labels:
    #     - TAG_ONE
    #     - TAG_TWO
    #     annotations:
    #     - name: test-annotation
    #       value: test-value
    # """
    # fabric_data = yaml.safe_load(fabric_yaml)
    # basic_copy = deepcopy(basic_yaml_data)
    # basic_copy["fabrics"] = fabric_data["fabrics"]
    
    # _run_test(name="Fabric creation", input=basic_copy)

    # # ----------- NODES -----------
    # node_yaml_1 = """
    # nodes:
    #   - name: Leaf01
    #     description: Leaf Node 01
    #     location: Rack1
    #     modelName: HF6100-32D
    #     roles:
    #      - LEAF
    #     serialNumber: SN-LEAF01
    #     psuAirflows:
    #       - airflow: AIRFLOW_TYPE_PORT_SIDE_INTAKE
    #         psuModel: PSU-123
    #     labels:
    #       - TAG_ONE
    # """

    # node_yaml_2 = """
    # nodes:
    #   - name: Spine01
    #     description: Spine Node 01
    #     location: Rack2
    #     modelName: HF6100-32D
    #     roles:
    #       - SPINE
    #     serialNumber: SN-SPINE01
    #     psuAirflows:
    #       - airflow: AIRFLOW_TYPE_PORT_SIDE_EXHAUST
    #         psuModel: PSU-456
    #     labels:
    #       - TAG_TWO
    # """

    # node_1_data = yaml.safe_load(node_yaml_1)["nodes"][0]
    # node_2_data = yaml.safe_load(node_yaml_2)["nodes"][0]
    # nodes_data = [node_1_data, node_2_data]
    # basic_copy = deepcopy(basic_yaml_data)
    # basic_copy["fabrics"][0]["nodes"] = nodes_data
    # delete_keys = ["connections", "vnis", "vrfs"]
    # for key in delete_keys:
    #     basic_copy["fabrics"][0].pop(key, None)

    # _run_test(name="Node creation", input=basic_copy)

    # # ----------- MANAGEMENT PORTS -----------
    # mgmt_yaml = """
    # managementPorts:
    #   - name: mgmt0
    #     description: Leaf mgmt
    #     configOrigin: CONFIG_ORIGIN_CLOUD
    #     connectedState: CONNECTED_STATE_CONNECTED
    #     ipv4ConfigType: CONFIG_TYPE_STATIC
    #     ipv4Address: 10.10.10.1/24
    #     ipv4Gateway: 10.10.10.254
    #     ipv6ConfigType: CONFIG_TYPE_STATIC
    #     ipv6Address: 2a02:1243:5687:0:9c09:2c7a:7c78:9ffc/33
    #     ipv6Gateway: 2a02:1243:5687:0:8d91:ba6b:b24d:9b41
    #     dnsAddresses:
    #       - 8.8.8.8
    #       - 8.8.4.4
    #     proxyAddress: http://proxy.example.com
    #     proxyPassword: secret
    #     proxyUsername: user1
    #     enabled: true
    #     setProxyPassword: true
    #     cloudUrls:
    #      - https://cloud.example.com
    #     noProxy:
    #       - localhost
    # """

    # mgmt_port_data = yaml.safe_load(mgmt_yaml)["managementPorts"]
    # basic_copy = deepcopy(basic_yaml_data)
    # basic_copy["fabrics"][0]["nodes"][0]["managementPorts"] = mgmt_port_data
    # delete_keys = ["connections", "vnis", "vrfs"]
    # for key in delete_keys:
    #     basic_copy["fabrics"][0].pop(key, None)

    # _run_test(name="Management port creation", input=basic_copy)

    # ----------- PORTS -----------
    port_yaml_1 = """
    ports:
      - name: Ethernet1_1
        description: Leaf routed port
        mtu: 9100
        fec: rs
        speed: 1x200G
        enabled: true
        roles:
          - ROUTED_PORT
        linkDown: false
        ipv4Addresses: 192.168.1.1
        ipv6Addresses: 2001:db8:1::1
        annotations:
          - name: test-annotation
            value: test-value
    """
    port_yaml_2 = port_yaml_1.replace("Ethernet1_1", "Ethernet1_2").replace("192.168.1.1", "192.168.1.2").replace("2001:db8:1::1", "2001:db8:1::2")
    port_1 = yaml.safe_load(port_yaml_1)["ports"][0]
    port_2 = yaml.safe_load(port_yaml_2)["ports"][0]
    ports_data = [port_1, port_2]
    basic_copy = deepcopy(basic_yaml_data)
    basic_copy["fabrics"][0]["nodes"][0]["ports"] = ports_data
    delete_keys = ["connections", "vnis", "vrfs"]
    for key in delete_keys:
        basic_copy["fabrics"][0].pop(key, None)

    _run_test(name="Port creation", input=basic_copy)
    return

    # ----------- CONNECTIONS -----------
    connections_yaml = """
    connections:
    - description: Leaf to Spine
        osType: HYPER_FABRIC
        pluggable: pluggable-conn
        local:
        portName: Ethernet1_1
        nodeName: Leaf01
        remote:
        portName: Ethernet1_2
        nodeName: Spine01
    - description: Spine to Leaf
        osType: HYPER_FABRIC
        pluggable: pluggable-conn
        local:
        portName: Ethernet1_2
        nodeName: Spine01
        remote:
        portName: Ethernet1_1
        nodeName: Leaf01
    """
    fabric["fabrics"][0]["connections"] = yaml.safe_load(connections_yaml)["connections"]
    _run_test(name="Connection creation", input=fabric)

    # ----------- VNIS -----------
    vni_yaml = """
    vnis:
    - name: vni01
        description: Test VNI 01
        vni: 1001
        mtu: 9100
        svis:
        - enabled: true
            ipv4Addresses:
            - 10.1.1.1
            ipv6Addresses:
            - 2001:db8:2::1
    - name: vni02
        description: Test VNI 02
        vni: 1002
        mtu: 9000
        svis:
        - enabled: true
            ipv4Addresses:
            - 10.2.2.1
            ipv6Addresses:
            - 2001:db8:3::1
        members:
        - untagged: false
            vlanId: 100
            port:
            nodeName: Leaf01
            portName: Ethernet1_1
    """
    fabric["fabrics"][0]["vnis"] = yaml.safe_load(vni_yaml)["vnis"]
    _run_test(name="VNI creation", input=fabric)

    # ----------- VRFS -----------
    vrf_yaml = """
    vrfs:
    - name: vrf01
        description: Customer VRF 1
        enabled: true
        asn: 64512
        vni: 1001
        labels:
        - TAG_BLUE
        annotations:
        - name: test-annotation
          value: test-value
    - name: vrf02
        description: Customer VRF 2
        enabled: true
        asn: 64513
        vni: 1002
        labels:
        - TAG_GREEN
        annotations:
        - name: test-annotation
          value: test-value
    """
    fabric["fabrics"][0]["vrfs"] = yaml.safe_load(vrf_yaml)["vrfs"]
    _run_test(name="VRF creation", input=fabric)

    # ----------- STATIC ROUTES -----------
    static_route_yaml_1 = """
    staticroute:
    - name: route1
        description: Default route
        enabled: true
        labels:
        - TAG_RED
        annotations:
        - name: test-annotation
          value: test-value
        routes:
        - nodeId: Leaf01
            interface: Ethernet1_1
            preference: 100
            prefix: 0.0.0.0/0
            nextHop: 10.1.1.254
            nextVrf: vrf01
            tag: TAG_AMBER
            discard: false
    """

    static_route_yaml_2 = static_route_yaml_1.replace("route1", "route2").replace("0.0.0.0/0", "192.168.0.0/16")
    static_1 = yaml.safe_load(static_route_yaml_1)["staticroute"]
    static_2 = yaml.safe_load(static_route_yaml_2)["staticroute"]
    fabric["fabrics"][0]["vrfs"][0]["staticroute"] = static_1
    fabric["fabrics"][0]["vrfs"][1]["staticroute"] = static_2
    _run_test(name="Static route creation", input=fabric)

if RUN_CREATION_TESTS:
    _run_creation_tests()