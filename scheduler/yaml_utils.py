import yaml


def read_yaml(yaml_file):
    '''读取yaml文件'''
    with open(yaml_file, 'r', encoding="utf-8") as f:
        values = yaml.load(f, Loader=yaml.Loader)
    # print(values)
    return values


def write_yaml(value_dict, yaml_file):
    '''写yaml文件'''
    with open(yaml_file, 'a', encoding="utf-8") as f:
        try:
            yaml.dump(data=value_dict, stream=f, encoding="utf-8", allow_unicode=True)
        except Exception as e:
            print(e)


def clean_yaml(yaml_file):
    '''清空yaml文件'''
    with open(yaml_file, 'w') as f:
        f.truncate()


if __name__ == '__main__':
    read_yaml('configure.yaml')
