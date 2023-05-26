class SNMPVarBind:
    """Класс для представления SNMP переменных.

    Attributes:
        oid (str): OID переменной.
        value (str): Значение переменной.
    """

    def __init__(self, oid: str, value: str) -> None:
        """
        Initializes a new instance of the class.

        :param oid: A string indicating the object id.
        :param value: A string indicating the value.

        :return: None
        """

        self.oid = oid
        self.value = value
        self.to_dict()

    def to_dict(self) -> dict:
        """
        Returns a dictionary representation of the object with the keys "oid" and "value".

        :return: A dictionary with keys "oid" and "value", representing the object.
        :rtype: dict
        """
        return {'oid': self.oid, 'value': self.value}
