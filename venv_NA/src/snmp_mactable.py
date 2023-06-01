from easysnmp import Session
from cachetools import LRUCache
from datetime import datetime
from config import config_data
from logger import Logger

logger = Logger('app.log')


class SNMPMACTable:
    def __init__(self,
                 ip_address: str,
                 community: str,
                 if_index: int,
                 version: int) -> None:
        """
        Initializes an instance of the class with the given IP address, community, interface index, and SNMP version.

        Args:
            ip_address (str): The IP address of the device.
            community (str): The SNMP community string used to access the device.
            if_index (int): The index of the interface for which the MAC addresses will be retrieved.
            version (int): The version of the SNMP protocol to be used.

        Returns:
            None
        """
        self.ip_address = ip_address
        self.community = community
        self.if_index = if_index
        self.version = version
        self.dot1dTpFdbPort_mib = '1.3.6.1.2.1.17.4.3.1.2'
        self.dot1dTpFdbAddress_mib = '1.3.6.1.2.1.17.4.3.1.1'
        self.ifIndex_mib = '1.3.6.1.2.1.17.1.4.1.2'
        self.cache = LRUCache(maxsize=config_data["cache_size"])

        # self.get_mac_table()
        self.get_mac_addresses()

    def _get_session(self) -> None:
        """
        Initializes and returns a session object if it has not already been created.

        :return: A Session object.
        """
        if not hasattr(self, 'session'):
            self.session = Session(hostname=self.ip_address,
                                   community=self.community,
                                   version=self.version)
            logger.log_info(f"Session object created for {self.ip_address}")

    def _get_mac_table(self) -> list:
        """
        Returns the MAC table of the device, either from the cache or by making a request to the device. 
        If the table is found in the cache and it is not older than 5 minutes, it is returned. 
        Otherwise, a request is made to the device to retrieve all ports and MAC addresses, 
        which are then grouped and returned as a list of dictionaries containing each MAC address and its interface index. 
        The resulting table is then cached. 
        This function takes no parameters and returns a list of dictionaries, 
        containing each MAC address and its corresponding interface index.
        """
        # Попытка найти таблицу в кэше
        # Если таблица найдена в кэше и ее возраст меньше 5 минут, возвращаем ее
        table = self.cache.get(self.ip_address)
        if table is not None:
            return table['mac_table']

        # Если таблица не найдена в кэше или ее возраст больше 5 минут, делаем запрос
        mac_table = []
        self._get_session()
        # Получение всех портов за один запрос
        port_entries = self.session.walk(self.dot1dTpFdbPort_mib)

        # Группировка портов по последнему номеру
        port_map = {port_entry.oid.split('.')[-1]: port_entry.value for port_entry in port_entries}

        # Получение всех MAC-адресов за один запрос и сопоставление их с портами
        mac_entries = self.session.walk(self.dot1dTpFdbAddress_mib)
        for mac_entry in mac_entries:
            last_number = mac_entry.oid.split('.')[-1]
            port_value = port_map.get(last_number)
            if port_value is not None:
                port = f'{self.ifIndex_mib}.{port_value}'
                if_index = self.session.get(port).value
                mac = ':'.join(f'{ord(i):02x}' for i in mac_entry.value)
                mac_table.append({'mac': mac, 'if_index': if_index})

        self.cache[self.ip_address] = {'mac_table': mac_table,
                                       'timestamp': datetime.now()}
        self.session = None
        return mac_table

    def get_mac_addresses(self) -> list:
        """
        Returns a list of MAC addresses associated with the interface identified by if_index.

        :return: A list of dictionaries with keys 'mac_address', 'vlan_id', 'interface', and 'static'
        :rtype: list
        """
        get_mac_table = self._get_mac_table()
        mac_addresses = [dict for dict in get_mac_table if int(dict['if_index']) == self.if_index]

        return mac_addresses


# get_mac_table = SNMPMACTable(self, ip='10.30.1.105', community='public', if_index=1, version=2)
