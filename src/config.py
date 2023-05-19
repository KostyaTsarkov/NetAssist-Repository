import json
import pathlib


config_data = {}


def load_config():
    global config_data
    parent_path = (pathlib.PurePath(__file__).parent)
    parent = str(parent_path.parents[0])
    config_file = str(parent)+'/config/config.json'
    with open(config_file, 'r') as config_file:
        config_data = json.load(config_file)


if not config_data:
    load_config()
