from easysnmp import Session


class SNMPInterface:
    """Класс для представления интерфейсов SNMP.

    Attributes:
        if_admin_status (int): Статус административного управления интерфейсом.
        if_oper_status (int): Статус операционного состояния интерфейса.
        if_in_errors (int): Количество ошибок входящего трафика на интерфейсе.
        if_out_errors (int): Количество ошибок исходящего трафика на интерфейсе.
        if_in_discards (int): Количество отброшенных пакетов входящего трафика на интерфейсе.
        if_out_discards (int): Количество отброшенных пакетов исходящего трафика на интерфейсе.
        if_index (int): Индекс интерфейса.
        mac_address (str): MAC-адрес подключенного устройства.
    """

    def __init__(self, ip_address: str,
                 community: str,
                 if_index: int,
                 version: int) -> None:
        """
        Инициализирует объект SNMPInterface.

        Args:
            ip_address (str): IP-адрес устройства.
            community (str): Имя коммьюнити.
            if_index (int): Индекс интерфейса.
        """
        self.ip_address = ip_address
        self.community = community
        self.if_index = if_index
        self.version = version
        self.session = Session(hostname=ip_address,
                               community=community,
                               version=2)
        self.if_admin_status = None
        self.if_oper_status = None
        self.if_in_errors = None
        self.if_out_errors = None
        self.if_in_discards = None
        self.if_out_discards = None
        self.mac_address = None
        
        self.get_interface_data()

    def get_interface_data(self) -> None:
        """Получает значения переменных для интерфейса."""
        
        """ ifAdminStatus = '1.3.6.1.2.1.2.2.1.7.'
        ifOperStatus = '1.3.6.1.2.1.2.2.1.8.'
        ifInErrors = '1.3.6.1.2.1.2.2.1.14.'
        ifOutErrors = '1.3.6.1.2.1.2.2.1.20.'
        ifInDiscards = '1.3.6.1.2.1.2.2.1.13.'
        ifOutDiscards = '1.3.6.1.2.1.2.2.1.19.'
        dot1dTpFdbAddress = '1.3.6.1.2.1.17.7.1.2.2.1.1.' """
        
        self.if_admin_status = self.get_if_admin_status(self.if_index)
        self.if_oper_status = self.get_if_oper_status(self.if_index)
        error_dict = self.get_if_errors(self.if_index)
        self.if_in_errors = error_dict.get('in_errors')
        self.if_out_errors = error_dict.get('out_errors')
        self.if_in_discards = error_dict.get('in_discards')
        self.if_out_discards = error_dict.get('out_discards')
        #self.mac_address = self.get_mac_address(self.if_index)
        self.to_dict()

    def to_dict(self) -> dict:
        """Преобразует объект SNMPInterface в словарь.

        Returns:
            dict: Словарь с ключами 'if_admin_status', 'if_oper_status',
            'if_in_errors', 'if_out_errors', 'if_in_discards',
            'if_out_discards', 'if_index' и 'mac_address'.
        """
        return {
            'if_admin_status': self.if_admin_status,
            'if_oper_status': self.if_oper_status,
            'if_in_errors': self.if_in_errors,
            'if_out_errors': self.if_out_errors,
            'if_in_discards': self.if_in_discards,
            'if_out_discards': self.if_out_discards,
            'if_index': self.if_index,
            'mac_address': self.mac_address
        }

    def get_if_admin_status(self, if_index):
        oid = f'1.3.6.1.2.1.2.2.1.7.{if_index}'
        response = self.session.get(oid)
        if_admin_status = int(response.value)

        if if_admin_status == 1:
            status = 'up'
        elif if_admin_status == 2:
            status = 'down'
        elif if_admin_status == 3:
            status = 'testing'
        else:
            status = 'unknown'

        return status

    def get_if_oper_status(self, if_index):
        oid = f'1.3.6.1.2.1.2.2.1.8.{if_index}'
        response = self.session.get(oid)
        if_oper_status = int(response.value)

        if if_oper_status == 1:
            status = 'up'
        elif if_oper_status == 2:
            status = 'down'
        elif if_oper_status == 3:
            status = 'testing'
        elif if_oper_status == 5:
            status = 'dormant'
        elif if_oper_status == 6:
            status = 'notPresent'
        elif if_oper_status == 7:
            status = 'lowerLayerDown'
        else:
            status = 'unknown'

        return status

    def get_if_errors(self, if_index):
        in_errors_oid = f'1.3.6.1.2.1.2.2.1.14.{if_index}'
        out_errors_oid = f'1.3.6.1.2.1.2.2.1.20.{if_index}'
        in_discards_oid = f'1.3.6.1.2.1.2.2.1.13.{if_index}'
        out_discards_oid = f'1.3.6.1.2.1.2.2.1.19.{if_index}'

        in_errors_response = self.session.get(in_errors_oid)
        out_errors_response = self.session.get(out_errors_oid)
        in_discards_response = self.session.get(in_discards_oid)
        out_discards_response = self.session.get(out_discards_oid)

        in_errors = int(in_errors_response.value)
        out_errors = int(out_errors_response.value)
        in_discards = int(in_discards_response.value)
        out_discards = int(out_discards_response.value)

        if in_errors == 0 and out_errors == 0 and in_discards == 0 and out_discards == 0:
            status = 'ok'
        else:
            status = 'error'

        return {'in_errors': in_errors, 'out_errors': out_errors, 'in_discards': in_discards, 'out_discards': out_discards, 'status': status}

    def get_mac_address(self, if_index):
        oid = f'1.3.6.1.2.1.2.2.1.6.{if_index}'
        response = self.session.get(oid)

        if len(response.value) == 0:
            return 'unknown'

        mac_address_bytes = response.asTuple()[0:6]
        mac_address_str = ':'.join(format(x, '02x') for x in mac_address_bytes)

        return mac_address_str

 
# interface = SNMPInterface('10.30.1.105', 'public', 3, 2)
# interface.get_interface_data()