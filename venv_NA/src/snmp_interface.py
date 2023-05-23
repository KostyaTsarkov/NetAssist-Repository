class SNMPInterface:
    """Класс для представления интерфейсов SNMP.

    Attributes:
        if_admin_status (int): Статус административного управления интерфейсом.
        if_oper_status (int): Статус операционного состояния интерфейса.
        if_in_errors (int): Количество ошибок входящего трафика на интерфейсе.
        if_out_errors (int): Количество ошибок исходящего трафика на интерфейсе.
        if_in_discards (int): Количество отброшенных пакетов входящего трафика на интерфейсе.
        if_out_discards (int): Количество отброшенных пакетов исходящего трафика на интерфейсе.
    """

    def __init__(self, if_admin_status: int, if_oper_status: int,
                 if_in_errors: int, if_out_errors: int, if_in_discards:
                     int, if_out_discards: int) -> None:
        """Инициализирует объект SNMPInterface.

        Args:
            if_admin_status (int): Статус административного управления интерфейсом.
            if_oper_status (int): Статус операционного состояния интерфейса.
            if_in_errors (int): Количество ошибок входящего трафика на интерфейсе.
            if_out_errors (int): Количество ошибок исходящего трафика на интерфейсе.
            if_in_discards (int): Количество отброшенных пакетов входящего трафика на интерфейсе.
            if_out_discards (int): Количество отброшенных пакетов исходящего трафика на интерфейсе.
        """
        self.if_admin_status = if_admin_status
        self.if_oper_status = if_oper_status
        self.if_in_errors = if_in_errors
        self.if_out_errors = if_out_errors
        self.if_in_discards = if_in_discards
        self.if_out_discards = if_out_discards

    def to_dict(self) -> dict:
        """Преобразует объект SNMPInterface в словарь.

        Returns:
            dict: Словарь с ключами 'if_admin_status', 'if_oper_status',
            'if_in_errors', 'if_out_errors', 'if_in_discards',
            'if_out_discards'.
        """
        return {
            'if_admin_status': self.if_admin_status,
            'if_oper_status': self.if_oper_status,
            'if_in_errors': self.if_in_errors,
            'if_out_errors': self.if_out_errors,
            'if_in_discards': self.if_in_discards,
            'if_out_discards': self.if_out_discards
        }
