from typing import Dict, Any, Optional
from flask import request, Response
from config import netbox_api
from config import config_data
import ipaddress
import pathlib
from ipv4 import IPv4Info
from jinja2 import Environment, FileSystemLoader
from macaddress import MAC
from pydhcpdparser import parser
from logger import Logger

logger = Logger('app.log')
ADDRESS_FAMILY_IPV4 = 4
ADDRESS_FAMILY_IPV6 = 6


def _configure_interface_ipv4_address(netbox_ip_address: str = '0.0.0.0') -> dict:
    """
    Configure the IPv4 address for an interface using Netbox IP address.

    :param netbox_ip_address: The Netbox IP address. Default is '0.0.0.0'.
    :type netbox_ip_address: str

    :return: A dictionary containing the IPv4 information extracted using the Netbox IP address.
    :rtype: dict

    If the provided Netbox IP address is invalid, an error message is logged.
    """
    try:
        ipv4_dict = IPv4Info().extract_info(netbox_ip_address)
    except ipaddress.AddressValueError as e:
        logger.log_error(f'Invalid address/netmask for IPv4 {netbox_ip_address}: {e}')
        ipv4_dict = {}

    return ipv4_dict


def _is_valid_mac_address(mac_address: Optional[str]) -> bool:
    """
    Check if a given MAC address is valid.

    Args:
        mac_address (Optional[str]): The MAC address to check.

    Returns:
        bool: True if the MAC address is valid, False otherwise.
    """
    if mac_address is None:
        logger.log_warning("MAC address is None...")
        return False

    try:
        MAC(mac_address)
        logger.log_info(f"MAC address is {mac_address} is valid.")
        return True
    except ValueError:
        logger.log_warning(f"MAC address {mac_address} is invalid.")
        return False


def _delete_config_file(device_name: str) -> None:
    """
    Deletes the configuration file for a given device name.

    :param device_name: the name of the device to delete the configuration for (str)
    :return: None
    """
    device_name = device_name.strip().casefold()
    parent_path = pathlib.Path(__file__).parent.parent
    conf_file = parent_path / str(config_data['dhcp_file'])
    conf_file = str(conf_file)

    with open(conf_file) as f:
        config = f.readlines()

    for line in config:
        if line.startswith('host'):
            if device_name in line.strip().casefold().split():
                start_index = config.index(line)
                for i in range(start_index + 1, len(config)):
                    if '}' in list(config[i]):
                        end_index = i
                        if start_index >= 0 and end_index >= start_index:
                            del config[start_index:end_index + 1]
                            with open(conf_file, 'w') as w:
                                w.writelines(config)
                            logger.log_info(f"'{device_name}' configuration deleted.")
                        else:
                            logger.log_error(f"Configuration file does not contain '{device_name}'.")
                        break


def _check_for_delete(mac_address: Optional[str],
                      device_name: Optional[str],
                      ip_address: Optional[str]) -> None:
    """
    This function checks if the given MAC address, device name, and IP address are valid. If the MAC address is not valid, 
    the function deletes the configuration file for the device. If the MAC address is valid, the function reads the 
    configuration file and checks if the MAC address and IP address are present in the file. If either of them is present, 
    the function logs the information and deletes the configuration file for the device.
    
    :param mac_address: A string containing the MAC address of the device.
    :param device_name: A string containing the name of the device.
    :param ip_address: A string containing the IP address of the device.
    :return: None
    """
    if not _is_valid_mac_address(mac_address):
        _delete_config_file(device_name)
        return

    hw_addr = mac_address.strip()
    ip_addr = ip_address.strip()

    parent_path = pathlib.Path(__file__).parent.parent
    conf_file = parent_path / str(config_data['dhcp_file'])
    conf_file = str(conf_file)

    with open(conf_file, 'a+') as f:
        f.seek(0)
        conf = f.read()
    config = parser.parse(conf)
    dic_config = config[0].get('host', {})
    if dic_config is None:
        return
    for dev_name in dic_config:
        mac_address = config[0]['host'][dev_name].get('hardware', {}).values()
        ip_address = config[0]['host'][dev_name].get('fixed-address', '')
        if hw_addr in mac_address or ip_addr in ip_address:
            logger.log_info(f"Find {hw_addr} or {ip_addr} for device {dev_name}")
            _delete_config_file(dev_name)

    """ for subnet in config.subnets:
        for host in subnet.hosts:
            if host.hardware == hw_addr or host.fixed_address == ip_addr:
                logger.log_info(f"Find {hw_addr} or {ip_addr} for device {host.name}")
                _delete_config_file(host.name) """


def _dhcpd_config_file(interface,
                       ip_address,
                       event: str = None) -> None:
    """
    Generates DHCP configuration file content for the given interface, IP address, and event.

    :param interface: The interface to generate DHCP configuration for.
    :type interface: Interface
    :param ip_address: The IP address associated with the interface.
    :type ip_address: dict
    :param event: The type of event that triggered the creation of the configuration file.
    :type event: str
    :return: None
    """
    ip_address = ip_address.get('ip4_address')
    host_name = interface.device.name
    mac_address = interface.mac_address
    interface_name = interface.name.replace(' ', '_')

    j2_host = f"{host_name}.{interface_name}"

    _check_for_delete(mac_address, j2_host, ip_address)

    if event not in ('delete', None):
        if _is_valid_mac_address(interface.mac_address):
            parent_path = pathlib.Path(__file__).parent.parent
            templates_path = parent_path / 'templates/'
            environment = Environment(loader=FileSystemLoader(templates_path))
            template = environment.get_template("dhcpd_static.template")
            content = template.render(
                device_name=j2_host,
                host_name=host_name,
                mac_address=mac_address,
                ip_address=ip_address
            )
            parent_path = pathlib.Path(__file__).parent.parent
            conf_file = parent_path / config_data['dhcp_file']
            with open(conf_file, 'a') as f:
                f.write(f"{content}\n")
            logger.log_info(f"File {config_data['dhcp_file']} is saved!")
        else:
            logger.log_error("MAC address isn’t compared.")


def _delete_ip_address(interface,
                       ip_address,
                       address_family: int) -> None:
    """
    Deletes an IP address on a network interface.

    Args:
        interface (object): The network interface object.
        ip_address (str): The IP address to remove.
        address_family (int): The address family of the IP address (IPv4 or IPv6).

    Returns:
        None
    """
    if address_family == ADDRESS_FAMILY_IPV4:
        ip_address = _configure_interface_ipv4_address(ip_address)
    else:
        logger.log_warning("IPv6 not supported")
        return
    logger.log_info(f"Removing address {ip_address} from interface '{interface.name}' on device '{interface.device.name}'...")

    _dhcpd_config_file(interface, ip_address, event='delete')


def _create_ip_address(interface,
                       ip_address,
                       address_family: int) -> None:
    """
    Create an IP address for a given interface and configure it based on the specified address family.

    :param interface: The interface to assign the IP address to.
    :param ip_address: The IP address to assign to the interface.
    :param address_family: The address family to use for the IP address. Must be 4 for IPv4 or 6 for IPv6.
    :return: None
    """
    if address_family == ADDRESS_FAMILY_IPV4:
        ip_address = _configure_interface_ipv4_address(ip_address)
    else:
        logger.log_warning("IPv6 not supported.")
        return
    logger.log_info(f"Assigning address {ip_address} to interface '{interface.name}' on device '{interface.device.name}'...")

    _dhcpd_config_file(interface, ip_address, event='create')


def _update_ip_address(interface,
                       snapshot_json: Dict[str, Any],
                       ip_address,
                       address_family: int) -> None:
    """
    Updates the IP address of a given interface based on a snapshot JSON. 
    Deletes the old IP address if the interface ID has changed. 

    :param interface: The interface object to update.
    :type interface: Any
    :param snapshot_json: The snapshot JSON to use for updating.
    :type snapshot_json: Dict[str, Any]
    :param ip_address: The new IP address to use.
    :type ip_address: Any
    :param address_family: The address family of the IP address.
    :type address_family: int
    :return: None
    :rtype: None
    """
    logger.log_info("Updating IP address.")
    if snapshot_json:
        try:
            old_interface_id = snapshot_json["prechange"]["assigned_object_id"]
            if old_interface_id != interface.id:
                old_interface_data = netbox_api.dcim.interfaces.get(old_interface_id)
                if not old_interface_data.mgmt_only:  # type: ignore
                    _delete_ip_address(interface, ip_address, address_family)
        except (AttributeError, ValueError) as e:
            logger.log_error(f"Address not previously assigned: {e}")

    if address_family == ADDRESS_FAMILY_IPV4:
        ip_address = _configure_interface_ipv4_address(ip_address)
    else:
        logger.log_warning("IPv6 not supported.")
        return

    _dhcpd_config_file(interface, ip_address, event='update')


def manage_ip() -> Response:
    """
    Manages IP addresses by retrieving device interface from NetBox API based on the assigned object id received
    in the request, and performing create, update, and delete operations based on the JSON event received in the request.
    If the address family is IPv4, the function checks if the device interface is for management only and logs accordingly.
    If the address family is IPv6, a warning is logged as IPv6 is not supported.
    If the address family is neither IPv4 nor IPv6, an error is logged and the function terminates.
    Returns a Response object with a status of 204.
    """
    if request.json:
        assigned_object_id = request.json["data"]["assigned_object_id"]
        device_interface = netbox_api.dcim.interfaces.get(assigned_object_id)
        device_ips = request.json["data"]["address"]
        address_family = request.json["data"]["family"]["value"]
        if address_family == ADDRESS_FAMILY_IPV4:
            if device_interface.mgmt_only:  # type: ignore
                logger.log_info("Management interface, no changes will be performed.")
            else:
                event_handlers = {
                    "deleted": _delete_ip_address,
                    "created": _create_ip_address,
                    "updated": _update_ip_address,
                }
                event = request.json["event"]
                handler = event_handlers.get(event)
                if handler == _update_ip_address:
                    handler(device_interface,
                            request.json.get("snapshots"),
                            device_ips,
                            address_family)
                else:
                    handler(device_interface,
                            device_ips,
                            address_family)
        elif address_family == ADDRESS_FAMILY_IPV6:
            logger.log_warning("IPv6 not supported.")
        else:
            logger.log_error(f"Invalid address family: {address_family}")

    return Response(status=204)
