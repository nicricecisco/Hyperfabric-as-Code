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
Create a YAML file detailing the specifications for your fabric. Checkout `user_submission_file.yaml` for a template on how to structure your YAML file. `validation_template.yaml` may also be helpful to look at the types and/or values required for specified fields.

## Sending to Hyperfabric
To upload your fabric specification to the Hyperfabric Cloud Controller, run the following command:

```
python3 main.py <your_yaml_file>.yaml
```

> Replace <your_yaml_file> with the actual name of your YAML configuration file.