from typing import List
from snmp_interface import SNMPInterface
from logger import Logger

logger = Logger('app.log')


class Database:
    """Класс для работы с базой данных.

    Attributes:
        db_name (str): Имя базы данных.
        connected (bool): Флаг, указывающий, установлено ли соединение с базой данных.
    """

    def __init__(self, db_name: str) -> None:
        """Инициализирует объект Database.

        Args:
            db_name (str): Имя базы данных.
        """
        self.db_name = db_name
        self.connected = False

    def connect(self) -> bool:
        """Устанавливает соединение с базой данных.

        Returns:
            bool: Флаг успешного соединения с базой данных.
        """
        # Код для установления соединения с базой данных
        self.connected = True
        logger.log_info('Connected to database.')
        return self.connected

    def disconnect(self) -> bool:
        """Разрывает соединение с базой данных.

        Returns:
            bool: Флаг успешного разрыва соединения с базой данных.
        """
        if not self.connected:
            return False

        # Код для разрыва соединения с базой данных
        self.connected = False
        logger.log_info('Disconnected from database.')
        return True

    def add_interface(self, interface: SNMPInterface) -> bool:
        """Сохраняет объект класса SNMPInterface в базу данных.

        Args:
            interface (SNMPInterface): Объект класса SNMPInterface.

        Returns:
            bool: Флаг успешного сохранения объекта в базу данных.
        """
        if not self.connected:
            return False

        # Код для сохранения объекта класса SNMPInterface в базу данных
        logger.log_info(f'Interface {interface} added to database.')
        return True

    def get_interfaces(self) -> List[SNMPInterface]:
        """Получает список объектов класса SNMPInterface из базы данных.

        Returns:
            List[SNMPInterface]: Список объектов класса SNMPInterface.
        """
        if not self.connected:
            return []

        # Код для получения списка объектов класса SNMPInterface из базы данных
        interfaces = []
        logger.log_info(f'Got {len(interfaces)} interfaces from database.')
        return interfaces
