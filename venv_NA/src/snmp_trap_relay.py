import requests
import urllib.parse
from config import config_data
from logger import Logger

logger = Logger('app.log')


class SNMPTrapRelay:
    """
    Класс для пересылки SNMP-трапов на сервер Flask.
    """

    def __init__(self, logger) -> None:
        """
        Initializes an instance of the class with a logger and configuration data.

        Args:
            logger: An instance of a logger object.

        Raises:
            ValueError: If the configuration data is missing.

        Returns:
            None
        """
        self.HEADERS = {'Content-type': 'application/json',
                        'Accept': 'text/plain'}
        try:
            self.logger = logger
            self.flask_host = config_data["flask_host"]
            self.flask_port = config_data["flask_port"]
            url_parts = ('http',
                         f'{self.flask_host}:{self.flask_port}',
                         'snmptrap',
                         '', '', '')
            self.url = urllib.parse.urlunparse(url_parts)

            self.timeout = config_data['session_post_timeout']
            self.session = requests.Session()
        except KeyError as e:
            raise ValueError("Отсутствуют данные конфигурации") from e

    def relay_SNMP_trap(self, trap_dict):
        """
        Sends a SNMP trap to the specified URL endpoint with the given trap_dict data.

        :param trap_dict: A dictionary containing the SNMP trap data.
        :type trap_dict: dict
        :return: None
        :raises: requests.exceptions.RequestException if there is an error sending the trap.
        """
        with self.session as s:
            try:
                with s.post(self.url,
                            json=trap_dict,
                            headers=self.HEADERS,
                            timeout=self.timeout) as response:
                    response.raise_for_status()
                self.logger.log_info(f"SNMP trap successfully sent to {self.url}")
            except requests.exceptions.RequestException as e:
                self.logger.log_error(f"Error sending SNMP trap to {self.url}: {e}")
