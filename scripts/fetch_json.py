import requests, json, os

API_URL = "https://hyperfabric.example.com/api/fabrics"
TOKEN = os.getenv("HYPERFABRIC_TOKEN")

headers = {"Authorization": f"Bearer {TOKEN}"}
response = requests.get(API_URL, headers=headers) # put in try catch or smthn
response.raise_for_status()

with open("data/fabrics.json", "w") as f:
    json.dump(response.json(), f, indent=2)
