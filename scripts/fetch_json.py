import requests, json, os
from pprint import pprint
from schemas.fabric_schema import validate_fabric

base_url = "https://hyperfabric.cisco.com/api/v1"
token = os.environ['HYPERFABRIC_TOKEN']

headers = {
  "Content-Type": "application/json",
  "Accept": "application/json",
  "Authorization": "Bearer " + token,
}

def get_fabrics():
    url = base_url + "/fabrics"
    response = requests.request('GET', url, headers=headers)
    fabrics = response.json()

    return fabrics['fabrics']



