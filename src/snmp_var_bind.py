class SNMPVarBind:
    """Класс для представления SNMP переменных.

    Attributes:
        oid (str): OID переменной.
        value (str): Значение переменной.
    """

    def __init__(self, oid: str, value: str) -> None:
        """Инициализирует объект SNMPVarBind.

        Args:
            oid (str): OID переменной.
            value (str): Значение переменной.
        """
        self.oid = oid
        self.value = value

    def to_dict(self) -> dict:
        """Преобразует объект SNMPVarBind в словарь.

        Returns:
            dict: Словарь с ключами 'oid' и 'value'.
        """
        return {'oid': self.oid, 'value': self.value}
