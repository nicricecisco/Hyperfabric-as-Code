import yaml

class IndentListDumper(yaml.SafeDumper):
    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, indentless=False)

def json_to_yaml(json):
    return yaml.dump(json, sort_keys=False, Dumper=IndentListDumper, default_flow_style=False)
