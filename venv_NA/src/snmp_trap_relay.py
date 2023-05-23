import json
import requests
from config import config_data


class SNMPTrapRelay:
    """
    Класс для пересылки SNMP-трапов на сервер Flask.
    """
    def __init__(self, logger):
        """
        Инициализирует класс логгером и данными конфигурации.

        :param logger: Логгер для записи событий.
        """
        try:
            self.logger = logger
            self.flask_host = config_data["flask_host"]
            self.flask_port = config_data["flask_port"]
            self.url = f'http://{self.flask_host}:{self.flask_port}/snmptrap'
            self.headers = {'Content-type': 'application/json',
                            'Accept': 'text/plain'}
        except KeyError as e:
            raise ValueError("Отсутствуют данные конфигурации") from e
        self.session = requests.Session()

    def relay_SNMP_trap(self, trap_dict):
        """
        Отправляет SNMP-трап на сервер Flask.

        :param trap_dict: Словарь с данными о трапе.
        """
        trap_json = json.dumps(trap_dict)
        with self.session as s:
            try:
                with s.post(self.url, data=trap_json,
                            headers=self.headers) as response:
                    response.raise_for_status()
                self.logger.log_info(f"SNMP-трап успешно отправлен на {self.url}")
            except requests.exceptions.RequestException as e:
                self.logger.log_error(f"Ошибка отправки SNMP-трапа на {self.url}: {e}")
