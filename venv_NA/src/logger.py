import logging


class Logger:
    """Класс для логирования сообщений.

    Attributes:
        log_file (str): Имя файла для логирования сообщений.
        logger (logging.Logger): Объект класса logging.Logger для записи сообщений в файл.
    """

    def __init__(self, log_file: str) -> None:
        """Инициализирует объект Logger.

        Args:
            log_file (str): Имя файла для логирования сообщений.
        """
        self.log_file = log_file
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def log_info(self, message: str) -> None:
        """Записывает информационное сообщение в лог.

        Args:
            message (str): Сообщение для записи в лог.
        """
        self.logger.info(message)

    def log_warning(self, message: str) -> None:
        """Записывает предупреждающее сообщение в лог.

        Args:
            message (str): Сообщение для записи в лог.
        """
        self.logger.warning(message)

    def log_error(self, message: str) -> None:
        """Записывает сообщение об ошибке в лог.

        Args:
            message (str): Сообщение для записи в лог.
        """
        self.logger.error(message)
