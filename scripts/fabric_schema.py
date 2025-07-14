from scripts.validate_schema import validate_against_schema

fabric_schema = {
    "address": {"type": "string"},
    "annotations": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "dataType": {"type": "string"},
                "name": {"type": "string"},
                "value": {"type": "string"}
            }
        }
    },
    "city": {"type": "string"},
    "country": {"type": "string"},
    "description": {"type": "string"},
    "fabricId": {"type": "string"},
    "labels": {"type": "list", "schema": {"type": "string"}},
    "location": {"type": "string"},
    "metadata": {
        "type": "dict",
        "schema": {
            "createdAt": {"type": "string"},
            "createdBy": {"type": "string"},
            "modifiedAt": {"type": "string"},
            "modifiedBy": {"type": "string"},
            "revisionId": {"type": "string"}
        }
    },
    "name": {"type": "string", "required": True},
    "topology": {"type": "string", "allowed": ["MESH", "SPINE_LEAF"]}  
}


def validate_fabric(fabric):
    errors = validate_against_schema(fabric, fabric_schema)
    return (len(errors) == 0), errors
