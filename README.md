# Hyperfabric-as-Code
A (YAML) conversion to/from the Hyperfabric cloud controller.

## Getting Started
Create an **API bearer token** in your Nexus Hyperfabric Dashboard. See https://developer.cisco.com/docs/hyperfabric/authentication/#bearer-tokens for more details. 

Set your `HYPERFABRIC_TOKEN` by either:
1. Running the following command in your terminal:
```
export HYPERFABRIC_TOKEN={bearerToken}
```

2. Or adding this line to a `.env` file in the root of your project:
```
HYPERFABRIC_TOKEN={bearerToken}
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

## List Available Devices
Run `get_devices.py` to retrieve a list of devices in your organization.

The full list will be saved to:
```
output/devices.py
```

To list **only unbound devices**, use the `--unbound` flag:
```
python3 get_devices.py --unbound
```

# Hyperfabric-as-Code Container
A container using code-server to host a web version of VS-Code including all required VS-Code extensions and python packages.
> Replace 'podman' with 'docker' in all of the following if using the Docker application

## Getting Started
Create an **API bearer token** for your github account. The required permissions are **read packages** and **read repositories**.

Set your `GITHUB_TOKEN` by running the following command in your terminal, only replacing GITHUB_TOKEN with your token and GITHUB_USERNAME with your username:
```
echo GITHUB_TOKEN | podman login ghcr.io -u GITHUB_USERNAME --password-stdin
```
Next, make sure you have a podman machine initialized and started with the following commands:
```
podman machine init
```
```
podman machine start
```
## Auto-Installation and Run Using `run_container.sh` 
Use the following commmand to run a shell script which will configure (if missing) and run (using named volume mounting) the container:
```bash
#Linux or MacOS
chmod +x run_container.sh && ./run_container.sh

#Windows -- must have git bash or bash installed
bash run_container.sh
```
## Manual Installation and Run

### Downloading the Container
To pull the latest version of the package, run the following command in your terminal:
```
podman pull ghcr.io/nicricecisco/hyperfabric-as-code-container:latest
```
### Running the Container
To run your container, run the following command in your terminal:
```
podman run -it --rm -p 8080:8080 --name hyperfabric-as-vscode hyperfabric-as-code-container
```
This will run the container under the name 'hyperfabric-as-vscode' in an interactive session listening on the localport 8080, which can be accessed via any web browser application.

### Running the Container Using Volume Mounting
To save your files between sessions of container running, you can use volume mounting with podman.

Use the following command to save your workspace in the container to a named volume called "hyperfabric_workspace":
```
podman run -it --rm -p 8080:8080 -v hyperfabric_workspace:/workspace --name hyperfabric-as-vscode hyperfabric-as-code-container
```
## Using the Container
On run, the container will automatically clone the Hyperfabric-as-Code repository (if not detected) or pull the latest version of the repo into your /workspace. From here, please reference the beginning of this README on how to set up your Hyperfabric API bearer token. 

## Helper Command Shortcuts

To simplify working in the container, the following shortcut functions are available in the terminal (defined in `.bashrc` during container build). These shortcut functions still work with any and all optional flags of the scripts for which they reference, and can be thought of as aliases.
>For all of the following, `$@` represents the file inputs.

- **`upload`** 
  Calls `python3 /workspace/main.py` to upload one or fabric YAML files to the Hyperfabric Cloud Controller.
  ```bash
  upload $@ 
- **`validate`**  
  Calls `python3 /workspace/validate_yaml.py` to validate one or more fabric YAML files without uploading.
  ```bash
  validate $@
- **`autocable`**  
  Calls `python3 /workspace/autocable.py` to autocable a fabric YAML file.
  ```bash
  autocable $@
- **`download`**  
  Calls `python3 /workspace/get_fabric_config.py` to download a fabric from the Hyperfabric Cloud Controller.
  ```bash
  download $@
- **`devices`**  
  Calls `python3 /workspace/get_devices.py` to get a list of devices.
  ```bash
  devices
- **`diff`**  
  Calls `python3 /workspace/run_diff.py` to get a diff between a fabric YAML file and the current configuration of that fabric on the Hyperfabric Cloud Controller.  
  ```bash
  diff $@
  ```
