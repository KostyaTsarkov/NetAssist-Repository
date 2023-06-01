# import logging
from easysnmp import Session
from config import config_data
from logger import Logger

logger = Logger('app.log')


class SNMPInterface:
    """
    Класс для представления интерфейсов SNMP.

    Attributes:
        if_admin_status (int): Статус административного управления интерфейсом.
        if_oper_status (int): Статус операционного состояния интерфейса.
        if_in_errors (int): Количество ошибок входящего трафика на интерфейсе.
        if_out_errors (int): Количество ошибок исходящего трафика на интерфейсе.
        if_in_discards (int): Количество отброшенных пакетов входящего трафика на интерфейсе.
        if_out_discards (int): Количество отброшенных пакетов исходящего трафика на интерфейсе.
        if_index (int): Индекс интерфейса.
    """

    def __init__(self,
                 ip_address: str,
                 community: str,
                 if_index: int,
                 version: int) -> None:
        """
        Initializes the object with the given ip_address, community, if_index, and version.
        :param ip_address: A string representing the IP address.
        :param community: A string representing the community.
        :param if_index: An integer representing the index.
        :param version: An integer representing the version.
        :return: None.
        """
        self.ip_address = ip_address
        self.community = community
        self.if_index = if_index
        self.version = version

        self.if_admin_status = None
        self.if_oper_status = None
        self.if_in_errors = None
        self.if_out_errors = None
        self.if_in_discards = None
        self.if_out_discards = None
        self.full_system_name = None
        self.neighbor_port = None
        self.neighbor_names = None

        self.max_attempts = int(config_data["snmp_session_retries"])
        self.session_timeout = int(config_data["snmp_session_timeout"])

        self.get_interface_data()

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

    def get_interface_data(self) -> None:
        """
        Retrieves interface data and updates class attributes if_admin_status, if_oper_status, if_in_errors,
        if_out_errors, if_in_discards, and if_out_discards with the retrieved data. Also, calls to_dict() to update
        the object's dictionary representation. Takes in no parameters and returns None.
        """
        self._get_session()
        if self.if_index is not None:
            self.if_admin_status = self._get_if_admin_status(self.if_index)
            self.if_oper_status = self._get_if_oper_status(self.if_index)
            error_dict = self._get_if_errors(self.if_index)
            self.if_in_errors = error_dict.get('in_errors')
            self.if_out_errors = error_dict.get('out_errors')
            self.if_in_discards = error_dict.get('in_discards')
            self.if_out_discards = error_dict.get('out_discards')
            self.full_system_name = self._get_sysname().get('sysname')
            neighbor_dict = self._get_lldp_neighbors_for_interface(self.if_index)
            self.neighbor_names = neighbor_dict.get('remote_hostname')
            self.neighbor_port = neighbor_dict.get('remote_port')
        self._to_dict()
        self.session = None

    def _to_dict(self) -> dict:
        """
        Return a dictionary containing the interface status information.

        :return: A dictionary containing the following keys:
                 - if_admin_status (bool): The administrative status of the interface.
                 - if_oper_status (bool): The operational status of the interface.
                 - if_in_errors (int): The number of inbound packets that contained errors.
                 - if_out_errors (int): The number of outbound packets that could not be transmitted because of errors.
                 - if_in_discards (int): The number of inbound packets that were discarded even though no errors were detected.
                 - if_out_discards (int): The number of outbound packets that were discarded even though no errors were detected.
                 - if_index (int): The interface index.
        :rtype: dict
        """

        return {
            'if_admin_status': self.if_admin_status,
            'if_oper_status': self.if_oper_status,
            'if_in_errors': self.if_in_errors,
            'if_out_errors': self.if_out_errors,
            'if_in_discards': self.if_in_discards,
            'if_out_discards': self.if_out_discards,
            'if_index': self.if_index,
            'full_system_name': self.full_system_name,
            'neighbor_names': self.neighbor_names,
            'neighbor_port': self.neighbor_port
        }

    def _get_if_admin_status(self,
                             if_index) -> str:
        """
        Returns the administrative status of a specified interface.

        :param if_index: an integer representing the index of the interface
        :return: a string indicating the administrative status of the interface. Possible values are 'up', 'down', 'testing', or 'unknown' if there is no match in the status_map.
        """
        oid = f'1.3.6.1.2.1.2.2.1.7.{if_index}'
        response = self.session.get(oid)
        if_admin_status = int(response.value)

        status_map = {
            1: 'up',
            2: 'down',
            3: 'testing',
        }
        status = status_map.get(if_admin_status, 'unknown')
        logger.log_info(f"Administrative status of interface {if_index} is {status}")

        return status

    def _get_if_oper_status(self,
                            if_index) -> str:
        """
        Returns the operational status of a network interface given its index.

        :param if_index: The index of the interface to query.
        :type if_index: int

        :return: The status of the interface, which can be one of the following values: up, down, testing, dormant, notPresent, lowerLayerDown, or unknown.
        :rtype: str
        """
        oid = f'1.3.6.1.2.1.2.2.1.8.{if_index}'
        response = self.session.get(oid)
        if_oper_status = int(response.value)

        status_map = {
            1: 'up',
            2: 'down',
            3: 'testing',
            5: 'dormant',
            6: 'notPresent',
            7: 'lowerLayerDown'
        }

        status = status_map.get(if_oper_status, 'unknown')
        logger.log_info(f"Operational status of interface {if_index} is {status}")

        return status

    def _get_if_errors(self,
                       if_index) -> dict:
        """
        Gets the input and output errors and discards for a given interface.

        :param if_index: The index of the interface to get the errors and discards for.
        :type if_index: int

        :return: A dictionary containing the input errors, output errors, input discards,
                 output discards, and the overall status of the interface.
        :rtype: dict
        """
        oids = [
            f'1.3.6.1.2.1.2.2.1.14.{if_index}',
            f'1.3.6.1.2.1.2.2.1.20.{if_index}',
            f'1.3.6.1.2.1.2.2.1.13.{if_index}',
            f'1.3.6.1.2.1.2.2.1.19.{if_index}',
        ]
        responses = self.session.get_bulk(oids)

        in_errors_response = responses[0]
        out_errors_response = responses[1]
        in_discards_response = responses[2]
        out_discards_response = responses[3]

        in_errors = int(in_errors_response.value)
        out_errors = int(out_errors_response.value)
        in_discards = int(in_discards_response.value)
        out_discards = int(out_discards_response.value)

        if in_errors == 0 and out_errors == 0 and in_discards == 0 and out_discards == 0:
            status = 'ok'
        else:
            status = 'error'

        logger.log_info(f"Interface {if_index}: In errors: {in_errors}, Out errors: {out_errors}, In discards: {in_discards}, Out discards: {out_discards}")

        return {'in_errors': in_errors,
                'out_errors': out_errors,
                'in_discards': in_discards,
                'out_discards': out_discards,
                'status': status}

    def _get_sysname(self) -> dict:
        """
        Get the system name by querying the device using SNMP.

        :return: A dictionary containing the system name.
        :rtype: dict
        """
        oid = '.1.3.6.1.2.1.1.5.0'
        response = self.session.get(oid)
        sysname = response.value

        logger.log_info(f"System name: {sysname}")

        return {'sysname': sysname}

    def _get_lldp_neighbors_for_interface(self, if_index) -> dict:
        """
        Returns a dictionary containing the remote hostname and port of the LLDP neighbors for a given interface index.

        :param if_index: An integer representing the index of the interface to query for LLDP neighbors.
        :type if_index: int
        :return: A dictionary containing the remote hostname and port of the LLDP neighbors.
        :rtype: dict
        """
        oids = [
            f'1.0.8802.1.1.2.1.4.1.1.9.{if_index}',
            f'1.0.8802.1.1.2.1.4.1.1.7.{if_index}'
        ]
        responses = self.session.get_next(oids)
        remote_port = responses[1].value
        remote_hostname = responses[0].value

        return {'remote_hostname': remote_hostname,
                'remote_port': remote_port}


# interface = SNMPInterface('10.30.1.105', 'public', 1, 2)
# interface.get_interface_data()
# interface.get_lldp_neighbors_for_interface(index=1)
