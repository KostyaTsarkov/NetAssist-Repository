import json
import pathlib
from logger import Logger
import pynetbox
from nornir import InitNornir
from credentials import (netbox_url,
                         netbox_token)

logger = Logger('app.log')


class Configuration:
    def __init__(self):
        self.config_data = {}
        self.load_config()
        self.create_netbox_api()
        self.create_nornir_session()

    def load_config(self) -> None:
        """
        Load configuration data from a JSON file and store it in the object's `config_data` attribute.
        :param self: The object instance.
        :return: None
        """
        parent_path = pathlib.Path(__file__).parent.parent
        config_file = parent_path / 'config' / 'config.json'
        config_file = str(config_file)

        try:
            with open(config_file, 'r') as config_file:
                self.config_data = json.load(config_file)
            logger.log_info('Configuration loaded successfully.')
        except Exception as e:
            logger.log_error(f'Error loading configuration: {e}')

    def load_inventory(self) -> None:
        """
        Loads the inventory by setting the paths for the inventory files. No parameters are taken.
        No values are returned.
        """
        base_path = pathlib.Path(__file__).parent.parent / 'inventory'
        group_file_path = base_path / 'groups.yml'
        defaults_file_path = base_path / 'defaults.yml'
        self.group_file = str(group_file_path)
        self.defaults_file = str(defaults_file_path)

    def create_nornir_session(self):
        """
        Creates a Nornir session using the NetBoxInventory2 plugin.

        :param netbox_url: str, the URL of the NetBox instance
        :param netbox_token: str, the NetBox API token
        :return: an InitNornir object

        :raises TypeError: if netbox_url or netbox_token are not strings
        :raises ValueError: if netbox_url does not start with 'http' or 'https'
        """
        if not isinstance(netbox_url, str) or not isinstance(netbox_token, str):
            raise TypeError("netbox_url and netbox_token must be strings")
        if not netbox_url.startswith(("http", "https")):
            raise ValueError("netbox_url must start with 'http' or 'https'")
        self.load_inventory()
        inventory = {
            "plugin": "NetBoxInventory2",
            "options": {
                "nb_url": netbox_url,
                "nb_token": netbox_token,
                "flatten_custom_fields": True,
                "include_vms": True,
                "config_context": True,
                "group_file": self.group_file,
                "defaults_file": self.defaults_file,
                # "group_file": "./inventory/groups.yml",
                # "defaults_file": "./inventory/defaults.yml",
            },
        }

        return InitNornir(inventory=inventory)

    def create_netbox_api(self):
        """
        Creates a new instance of the pynetbox API client for NetBox. 

        :return: A pynetbox.api object.
        """
        nr = self.create_nornir_session()
        if nr is None:
            logger.log_error('Could not connect to device.')
        else:
            nb_url = nr.config.inventory.options['nb_url']
            nb_token = nr.config.inventory.options['nb_token']
            return pynetbox.api(nb_url,
                                token=nb_token,
                                threading=True)


config = Configuration()
nornir_session = config.create_nornir_session()
netbox_api = config.create_netbox_api()
config_data = config.config_data
