import json
import requests
from config import config_data


class SNMPTrapRelay:
    def __init__(self):
        self.flask_host = config_data["flask_host"]
        self.flask_port = config_data["flask_port"]
        self.url = f'http://{self.flask_host}:{self.flask_port}/snmptrap'

    def relay_SNMP_trap(self, trap_dict):
        """
        Отправляет SNMP-трап на сервер Flask

        :param trap_dict: словарь с данными о SNMP-трапе
        """
        trap_json = json.dumps(trap_dict)
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        response = requests.post(self.url, data=trap_json, headers=headers)

        if response.status_code == 200:
            print(f"SNMP Trap successfully sent to {self.url}")
        else:
            print(f"Error sending SNMP Trap to {self.url}")
