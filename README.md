# Hyperfabric-as-Code
A (YAML) conversion to/from the Hyperfabric cloud controller.

## Getting Started
Create an **API bearer token** in your Nexus Hyperfabric Dashboard. See https://developer.cisco.com/docs/hyperfabric/authentication/#bearer-tokens for more details. 

> Make sure to set the Scope to **Admin**.

Initialize `HYPERFABRIC_TOKEN` by running the following in your terminal:
```
export HYPERFABRIC_TOKEN={bearerToken}
```

## Creating a YAML File
Create a YAML file detailing the specifications for your fabric. Checkout `user_submission_file.yaml` for a template on how to structure your YAML file. `schemas/validation/validation_template.yaml` may also be helpful to look at the types and/or values required for specified fields.

### Example
```
fabrics:
  - name: example-fabric
    description: My example fabric
    location: CA-95134
    address: 300 East Tasman Drive
    city: Milpitas
    country: US
    labels:
      - TAG_ONE
      - TAG_TWO
    topology: SPINE_LEAF
    
    nodes:
      - name: Leaf01
        description: Leaf Switch 01
        modelName: HF6100-32D
        roles: [LEAF]
```

## Sending to Hyperfabric
To upload your fabric specification(s) to the Hyperfabric Cloud Controller, run the following command:

```
python3 main.py <file1>.yaml [<file2>.yaml ...]
```

> Replace `<file1>.yaml`, `<file2>.yaml`, etc. with the actual names of your YAML configuration files.
You may provide one or multiple files in a single command.

## Validating YAML Input
The `main.py` script automatically validates your YAML input files before uploading them to the Hyperfabric Cloud Controller.

If you want to validate your YAML files **without uploading**, use the standalone `validate_yaml.py` script:

```
python3 validate_yaml.py <your_yaml_file>.yaml
```

You can also validate multiple YAML files at once:
```
python3 validate_yaml.py file1.yaml file2.yaml ...
```

## Autocabling
Autocabling can be configured in two ways:

1. By specifying the `autocabling` attribute in your YAML input file.

2. By using the standalone script `autocable.py`.

### 1. Autocabling via YAML Attribute
To enable autocabling directly in your fabric configuration, include the `autocabling` block:

```
fabrics:
  - name: from-python
    autocabling:
      enabled: true
    ...
```
You can specify a cable using the `pluggable` field, along with optional fields such as `speed`, `length`, `cablePreference`, and `portType`.

> See `schemas/validation/validation_template.yaml` for the full list of supported options and validation rules.

Autocabling behavior:

1. In a `MESH` topology, each leaf switch will be connected once to every other leaf.

2. In a `SPINE_LEAF` topology, each spine will be connected once to every leaf.

To upload the YAML file and apply autocabling, run:
```
python3 main.py <your_yaml_file>.yaml
```

You can also pass multiple YAML files:
```
python3 main.py file1.yaml file2.yaml ...
```

### 2. Autocabling via `autocable.py`
The autocable.py script supports two input modes:

1. A **fabric name** (for an existing fabric in the system).

2. A **YAML file** (for an unuploaded or hypothetical fabric definition).

#### Input: Fabric Name
Run:
```
python3 autocable.py my-fabric-name
```

#### Input: YAML File
Run:
```
python3 autocable.py <your_yaml_file>.yaml
```

#### Output
The script will generate two files in the `output/` directory:

* `autocable_output.yaml`: A set of autocabled connections (ready to be uploaded).

* `removed_connections.yaml`: A list of existing connections that should be removed to conform to standard autocabling logic.

To upload the results to the Hyperfabric Cloud Controller:
```python
# If using fabric name input
python3 main.py output/autocable_output.yaml output/removed_connections.yaml

# If using YAML input
python3 main.py output/autocable_output.yaml
```

## Exporting a Fabric to YAML
To generate a YAML configuration from an existing fabric in the Hyperfabric Cloud Controller, run:

```
python3 get_fabric_config_to_yaml.py <fabric-name>
```
> Replace `<fabric-name>` with the name of the existing fabric.

The YAML file will be saved to:
```
output/<fabric-name>.yaml
```

## Getting a List of Devices

This script retrieves device information from the Hyperfabric API and writes it to a YAML file. It supports optional filtering to output only unbound devices.

Usage
python3 get_devices.py [--unbound]

Options
Flag	Description
--unbound	Only output devices that are not bound to nodes (filtered by nodeId)
Output

The script generates a YAML file at:

output/devices.yaml


Each run includes a timestamp comment at the top of the file:

# Generated on 2025-08-14T09:00:00Z
devices:
  - deviceId: abc123
    serialNumber: SN001
    modelName: XF-1000
    name: leaf1
  - deviceId: def456
    serialNumber: SN002
    modelName: XF-1000
    name: leaf2


If no devices are returned from the API, the file contains only the timestamp comment.

Description

fetch_devices() — Queries the Hyperfabric API and handles HTTP and network errors.

filter_attributes(devices) — Optional function to return only unbound devices with selected fields (deviceId, serialNumber, modelName, name).

main(only_unbound=False) — Orchestrates fetching, optional filtering, and writing YAML output.

parse_args() — Handles the --unbound command-line argument.

Logging

The script uses a logger (utils.logger.get_logger) to provide information and error messages during execution.