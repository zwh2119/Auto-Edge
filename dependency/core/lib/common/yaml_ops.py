import yaml


class YamlOps:

    @staticmethod
    def read_yaml(yaml_file):
        with open(yaml_file, 'r', encoding="utf-8") as f:
            values = yaml.load(f, Loader=yaml.Loader)
        return values

    @staticmethod
    def write_yaml(value_dict, yaml_file):
        with open(yaml_file, 'a', encoding="utf-8") as f:
            yaml.dump(data=value_dict, stream=f, encoding="utf-8", allow_unicode=True)

    @staticmethod
    def clean_yaml(yaml_file):
        with open(yaml_file, 'w') as f:
            f.truncate()
