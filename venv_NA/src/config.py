import json
import pathlib
from logger import Logger

logger = Logger('app.log')


class Configuration:
    def __init__(self):
        self.config_data = {}
        self.load_config()

    def load_config(self):
        parent_path = pathlib.Path(__file__).parent.parent
        config_file = parent_path / 'config' / 'config.json'
        config_file = str(config_file)

        try:
            with open(config_file, 'r') as config_file:
                self.config_data = json.load(config_file)
            logger.log_info('Configuration loaded successfully.')
        except Exception as e:
            logger.log_error(f'Error loading configuration: {e}')


config = Configuration()
config_data = config.config_data
