from easysnmp import Session
from cachetools import TTLCache
from datetime import datetime


class SNMPMACTable:
    def __init__(self, ip='10.30.1.105', community='public', version=2):
        self.ip = ip
        self.community = community
        self.version = version
        self.dot1dTpFdbPort_mib = '1.3.6.1.2.1.17.4.3.1.2'
        self.dot1dTpFdbAddress_mib = '1.3.6.1.2.1.17.4.3.1.1'
        self.ifIndex_mib = '1.3.6.1.2.1.17.1.4.1.2'
        self.cache_ttl_seconds = 300
        self.cache_max_size = 1000
        self.cache = TTLCache(maxsize=self.cache_max_size, ttl=self.cache_ttl_seconds)
        self.session = Session(hostname=self.ip, community=self.community, version=self.version)

        self.get_mac_table()

    def get_mac_table(self):
        # Попытка найти таблицу в кэше
        # Если таблица найдена в кэше и ее возраст меньше 5 минут, возвращаем ее
        table = self.cache.get(self.ip)
        if table is not None:
            return table['mac_table']

        # Если таблица не найдена в кэше или ее возраст больше 5 минут, делаем запрос
        mac_table = []

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

        # Кэшируем таблицу на 5 минут
        self.cache[self.ip] = {'mac_table': mac_table, 'timestamp': datetime.now()}

        return mac_table


get_mac_table = SNMPMACTable()
