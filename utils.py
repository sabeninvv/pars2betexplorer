import yaml
from random import randint


def file_operation(path, mode, yaml_file=False, data=None):
    with open(path, mode=mode) as file:
        if mode == 'r' and not yaml_file:
            data = file.read()
            return data.split('\n')
        elif mode == 'r' and yaml_file:
            data = yaml.safe_load(file)
            return data
        elif mode == 'w' and yaml_file:
            yaml.dump(data, file, default_flow_style=False)


def load_ua():
    with open('track/ua.yaml', 'r') as file:
        ua = yaml.safe_load(file)
        inx = randint(0, len(ua) - 1)
        ua = ua[inx]
    return str(ua)


def get_config():
    config_dict = file_operation(path='config/config.yaml', mode='r', yaml_file=True)
    return str(config_dict['PASS_FOR_TOR']), int(config_dict['PORT_FOR_TOR']), str(config_dict['BOT_TOKEN']), str(config_dict['BIN_LOCATION'])