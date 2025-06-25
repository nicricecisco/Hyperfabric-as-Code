import scripts.fetch_json
import scripts.json_to_yaml
import scripts.yaml_to_tf

if __name__ == "__main__":
    fabrics = scripts.fetch_json.get_fabrics()
    
    for fabric in fabrics:
        print(fabric)