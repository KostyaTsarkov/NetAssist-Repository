from ipaddress import AddressValueError
import re
from typing import Any, Optional
from ipv4 import IPv4Info
from logger import Logger

logger = Logger('app.log')
INTERFACE_REGEX = re.compile(r"^(\D+)(\d+.*)$")


class DeviceManagementAddress:

    @classmethod
    def get_address(cls, device_interface: Any) -> Optional[str]:
        """
        Given a device_interface, this method returns its IPv4 address if it exists.
        If the device_interface is None, or has no name or no device, None is returned.
        If the interface name is invalid or cannot be parsed, None is returned.

        :param device_interface: An instance of `Any` class representing the device_interface.
        :type device_interface: Any

        :return: Returns the IPv4 address of the device_interface if it exists, else `None`.
        :rtype: Optional[str]
        """
        if not device_interface or not device_interface.name:
            return None

        interface_type, interface_id = cls._parse_interface_name(device_interface.name)

        if not device_interface.device or not device_interface.device.primary_ip:
            return None

        primary_ip = device_interface.device.primary_ip

        ipv4_address = cls._configure_interface_ipv4_address(primary_ip)
        if ipv4_address is not None:
            return ipv4_address['ip4_address']

        return None

    @staticmethod
    def _parse_interface_name(interface_name: str) -> tuple:
        """
        Given an interface name as a string, this static method parses it into
        two separate strings representing the interface type and its ID. The
        function raises a ValueError if the provided interface name doesn't
        match the expected format. The return value is a tuple with two strings,
        the interface type and its ID.

        :param interface_name: A string representing the name of the interface
        :type interface_name: str
        :return: A tuple with two strings representing the interface type and its ID
        :rtype: tuple
        :raises ValueError: If the provided interface name doesn't match the expected format
        """
        match = INTERFACE_REGEX.fullmatch(interface_name)
        if not match:
            raise ValueError("Invalid interface name")
        interface_type, interface_id = match.groups()

        return interface_type, interface_id

    @staticmethod
    def _configure_interface_ipv4_address(netbox_ip_address: str = '0.0.0.0') -> dict:
        """
        This is a static method that configures an IPv4 address for a given NetBox IP address.

        :param netbox_ip_address: A string that represents the NetBox IP address. Defaults to '0.0.0.0'
        :type netbox_ip_address: str

        :return: A dictionary containing the IPv4 address information.
        :rtype: dict
        """
        try:
            ipv4_dict = IPv4Info().extract_info(netbox_ip_address)
        except AddressValueError as e:
            logger.log_error(f'Invalid address/netmask for IPv4 {netbox_ip_address}: {e}')
            ipv4_dict = {}

        return ipv4_dict
