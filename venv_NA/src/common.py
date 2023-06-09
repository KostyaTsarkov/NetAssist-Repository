from typing import Any, Dict, List, Optional, Union
import re
from deepdiff import DeepDiff
import pathlib
from flask import request, Response
from config import netbox_api, nornir_session
from types import SimpleNamespace
import time
from multiping import multi_ping
from jinja2 import Environment, FileSystemLoader, TemplateError
from nornir_napalm.plugins.tasks import napalm_get
from nornir_netmiko.tasks import netmiko_send_config
from nb_device_mng_address import DeviceManagementAddress
from logger import Logger
from ipaddress_or_dns import resolver
import traceback

logger = Logger('app.log')


def compare(prechange, postchange):
    """
    Compares two objects and returns a dictionary of changes between the two.

    :param prechange: The original object to compare.
    :type prechange: Any
    :param postchange: The object to compare against.
    :type postchange: Any
    :return: A dictionary of changes between the two objects. If there are no changes, returns None.
    :rtype: Union[Dict[str, Any], None]
    """
    compare = DeepDiff(prechange,
                       postchange,
                       exclude_paths="root['last_updated']")
    change = {}
    change_key = []
    new_value = []

    for key in compare.keys():
        if key == 'values_changed' or key == 'type_changes':
            for inkey in compare[key].keys():
                change_key.append(re.findall("'([^']*)'", inkey)[0])
                new_value.append(compare[key][inkey]['new_value'])
    change = dict(zip(change_key, new_value))
    if len(change) == 0:
        change = None

    return change


def convert_none_to_str(value: str or None) -> str:
    """
    Convert a given value to a string. If the value is None, an empty string is returned.

    :param value: A string or None value to be converted.
    :type value: str or None
    :return: A string representation of the given value or an empty string if the value is None.
    :rtype: str
    """
    return str(value) if value else ''


def fill_template(*args: Any, **kwargs: str) -> Optional[str]:
    """
    Fills a Jinja2 template with provided arguments.

    Args:
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.

    Keyword Args:
        template_file (str): The filename of the Jinja2 template
            to be used.

    Returns:
        Optional[str]: The rendered template content, or None
        if there was not enough data to fill out the template.
    """
    parent_path = pathlib.Path(__file__).parent.parent
    templates_path = parent_path / 'templates/'
    environment = Environment(loader=FileSystemLoader(templates_path))
    template = environment.get_template(kwargs['template_file'])
    content = None
    event = kwargs['event']
    interface = kwargs['interface']

    try:
        if event == 'shutdown':
            content = template.render(interface_name=convert_none_to_str(interface.name))
        else:
            content = template.render(
                interface_name=convert_none_to_str(interface.name),
                descr=convert_none_to_str(interface.description),
                access_vlan=convert_none_to_str(interface.untagged_vlan.vid),
                mode=convert_none_to_str(interface.mode.value)
                )
    except TemplateError:
        pass

    return content


def get_cisco_interface_config(interface,
                               event='None'):
    """
    Generates Cisco interface configuration based on the interface name and
    event type.

    :param interface: (str) Interface name.
    :param event: (str) Type of event to generate configuration for.
    Default is 'None'.
    :return: (str) Generated configuration content.
    """
    template_lookup = {'shutdown': 'cisco_ios_shutdown_interface.template',
                       'delete': 'cisco_ios_default_interface.template'}
    template_file = template_lookup.get(event,
                                        'cisco_ios_access_interface.template')

    content = fill_template(interface=interface,
                            template_file=template_file,
                            event=event)
    return content


def push_interface_config(netbox_interface,
                          content: str,
                          event: Optional[str] = None,
                          config_context=None) -> None:
    """
    Pushes the provided configuration content to the specified interface on the given
    netbox_interface. It first checks if the device role of the netbox_interface is
    among the network_devices_roles stored in the config_context. If it is, it proceeds
    to ping the specified interface to ensure availability. If it is available, the
    function attempts to connect to the device and retrieves all interfaces. If the
    specified interface is present, it applies the provided configuration content to it
    and outputs a success message. If the interface is not found, it outputs a warning.
    If the device cannot be connected to, it outputs an error. If the device role of
    the netbox_interface does not match the network_devices_roles, it outputs an info
    message.

    :param netbox_interface: The interface to which the configuration content will be applied.
    :type netbox_interface: Any
    :param content: The configuration content to apply to the specified interface.
    :type content: str
    :param event: Optional event to associate with the function call.
    :type event: str, optional
    :param config_context: A dictionary containing various configuration parameters.
    :type config_context: dict, optional
    :return: None
    :rtype: None
    """
    device_role = netbox_interface.device.device_role.slug
    device_name = netbox_interface.device.name
    network_devices_roles = config_context.network_devices_roles

    if device_role in network_devices_roles:
        attempts = config_context.attempts
        attempt_timeout = config_context.attempt_timeout
        fail_count = config_context.fail_count
        name = netbox_interface.name
        addrs = []
        filter_query = DeviceManagementAddress().get_address(netbox_interface)
        addrs.append(filter_query)
        timeout = config_context.timeout
        retry = int(config_context.retry)
        ignore_lookup_errors = eval(config_context.ignore_lookup_errors)

        responses, no_responses = multi_ping(addrs,
                                             timeout,
                                             retry,
                                             ignore_lookup_errors
                                             )
        logger.log_info("icmp ping.")

        # if filter_query in list(responses.keys()):
        if resolver.resolve(filter_query):
            logger.log_info(f'{addrs} is available.')
            nr = nornir_session
            if nr is None:
                logger.log_error('Could not connect to device.')
                # logger.log_warning(f'{no_responses}')
            else:
                with nr:
                    filtered_nr = nr.filter(hostname=filter_query)
                    if len(filtered_nr.inventory.hosts) == 0:
                        logger.log_error('Could not filtered.')
                        filtered_nr = nr.filter(hostname=device_name)
                    #with nr.filter(hostname=filter_query) as sw:
                    with filtered_nr as sw:
                        sw.inventory.hosts[device_name].username = config_context.device_username
                        sw.inventory.hosts[device_name].password = config_context.device_password
                        sw.inventory.hosts[device_name].hostname = resolver.resolve(filter_query)
                        # get_int = sw.run(task=napalm_get, getters=['get_interfaces'])
                        for _ in range(attempts):
                            get_int = sw.run(task=napalm_get, getters=['get_interfaces'])
                            logger.log_info(f'Attempting to connect {(_ + 1)}.')
                            if get_int.failed is True:
                                fail_count += 1
                                time.sleep(attempt_timeout)
                            else:
                                logger.log_info('Connection state is connected.')
                                for device in get_int.values():
                                    interfaces = device.result['get_interfaces'].keys()
                                    if name in (intf for intf in list(interfaces)):
                                        logger.log_info(f"Find {name} for device {device.host}.")
                                        result = sw.run(netmiko_send_config,
                                                        name="Configuration interface.../",
                                                        config_commands=content)
                                        comment = 'All operations are performed'
                                        logger.log_info(comment)
                                break
                        if fail_count >= attempts:
                            comment = f'Could not connect to {addrs}'
                            logger.log_error(comment)
                logger.log_info("Connection state is closed.")
        elif filter_query in no_responses:
            comment = '{} is not available'.format(addrs)
            logger.log_warning(comment)
    else:
        comment = f'Devices must match the list of {network_devices_roles}'
        logger.log_info(comment)


def change_config_intf(netbox_interface,
                       event: str,
                       config_context) -> None:
    """
    This function changes the configuration of a given network interface by first getting the configuration
    from a Cisco device using the get_cisco_interface_config() function. If the configuration is not None, then
    it is pushed to the given network interface using the push_interface_config() function. The logger logs
    information about whether the configuration change was successful or not. If the configuration is None,
    then the logger logs that no data was returned from get_cisco_interface_config(). If an exception is
    thrown while executing the function, then the logger logs that no data was found for the given interface
    and event. This function takes in three parameters: 
        1. a netbox_interface object representing the network interface to be configured,
        2. a string event representing the type of event that triggered the configuration change,
        3. a netbox_config_context object representing the configuration context for the network interface.
    It returns None.
    """
    try:
        content = get_cisco_interface_config(netbox_interface, event)
        if content is not None:
            # content = '\n'.join(content)
            push_interface_config(netbox_interface,
                                  content,
                                  event,
                                  config_context)
            logger.log_info(f"{event.capitalize()} interface {netbox_interface} config.")
        else:
            logger.log_info("No data returned from cisco_config_interface()")
    except Exception:
        logger.log_error(traceback.format_exc())
        logger.log_info(f'No data for {event.lower()} {netbox_interface.name}')


def manage_connected_interfaces(intf: Dict[str, Any],
                                event: str,
                                role: str,
                                config_context) -> None:
    """
    Manages connected interfaces based on the given parameters.

    :param intf: A dictionary representing the interface.
    :type intf: Dict[str, Any]
    :param event: A string representing the event.
    :type event: str
    :param role: A string representing the role.
    :type role: str
    :param config_context: The context of the configuration.
    :type config_context: Any
    :return: None
    :rtype: None
    """
    network_device_roles = config_context.network_devices_roles
    user_device_roles = config_context.user_devices_roles

    def create_changes_dict(network_device_id: int,
                            user_intf: Dict[Any, Any]) -> List[Dict[Any, Union[Any, Any]]]:
        """
        Creates a dictionary containing changes to a network device interface based on the supplied parameters.

        :param network_device_id: An integer representing the ID of the network device.
        :param user_intf: A dictionary containing user-supplied interface changes.
        :type network_device_id: int
        :type user_intf: Dict[Any, Any]
        :return: A list containing a dictionary of the changes to be made.
        :rtype: List[Dict[Any, Union[Any, Any]]]
        """
        changes = {}
        change_key = ['id']
        new_value = [network_device_id]
        for value in user_intf:
            if value[0] in config_context.interface and value[1] not in ['', None]:
                change_key.append(value[0])
                if isinstance(value[1], dict):
                    new_value.append(list(value[1].values())[0])
                else:
                    new_value.append(value[1])
        changes = dict(zip(change_key, new_value))
        return [changes]

    if role in user_device_roles and event != 'delete':
        if intf['connected_endpoints_reachable']:
            network_device_id = intf['connected_endpoints'][0]['id']
            changes = create_changes_dict(network_device_id, intf)
            netbox_api.dcim.interfaces.update(changes)
        else:
            comment = f"Neighbor is not reachable for {intf}"
            logger.log_info(comment)
    elif role in network_device_roles and event != 'delete':
        if intf['connected_endpoints_reachable']:
            network_intf = netbox_api.dcim.interfaces.get(intf['connected_endpoints'][0]['id'])
            network_device_id = intf.id  # type: ignore
            if network_intf and network_device_id:
                changes = create_changes_dict(network_device_id, network_intf)
                netbox_api.dcim.interfaces.update(changes)
        else:
            comment = f"Neighbor is not reachable for {intf}"
            logger.log_warning(comment)
    elif role in network_device_roles and event == 'delete':
        changes = dict.fromkeys(config_context.interface, None)
        changes['description'] = ""
        changes['id'] = intf.id  # type: ignore
        changes['enabled'] = False

        netbox_api.dcim.interfaces.update([changes])
        logger.log_info(f"Clear {intf} netbox interface config")


def mng_cable() -> Response:
    """
    This function manages a cable connection between devices. The function receives a 
    request that contains a JSON body. The JSON body contains a dictionary with a key 'data'
    which holds information about the cable. The function parses this data and extracts the 
    names, roles, and IDs of the devices that are connected by the cable. It then checks whether
    the devices have the right roles defined in their configuration contexts. If not, it logs a
    warning message. If the devices have the right roles, the function gets the interface ID of
    the device that has the role defined first in the configuration context. It then checks the 
    mode of the interface and performs certain actions based on the event type. If the event type
    is 'created' or 'deleted', the function performs some operations on the interface. If the 
    event type is 'updated', the function updates the configuration of the interface. If the 
    interface is a management interface, the function logs a message indicating that no changes 
    will be performed. If the interface is in tagged mode, the function logs a message indicating 
    the mode. Finally, the function returns a response object with a status code of 204.
    """
    try:
        device_keys = ['role', 'device_id', 'intf_id']
        devices = []
        device_names = []
        device_roles = []
        TERMINATIONS_REGEX = "[a|b]_terminations"
        device_intf_id = int

        if request.json:
            cable_data = request.json['data']
            event_type = request.json["event"]
            pre_change_snapshot = request.json['snapshots']['prechange']
            post_change_snapshot = request.json['snapshots']['postchange']
            for cable_key in cable_data.keys():
                if re.match(TERMINATIONS_REGEX, cable_key) and len(cable_data[cable_key]) == 1:
                    for i in range(len(cable_data[cable_key])):
                        device_id = cable_data[cable_key][i]['object']['device']['id']
                        device_values = []
                        device_names.append(
                            netbox_api.dcim.devices.get(
                                device_id).name)  # type: ignore
                        device_values.append(
                            netbox_api.dcim.devices.get(
                                device_id).device_role.slug)  # type: ignore
                        device_values.append(
                            device_id)
                        device_values.append(
                            cable_data[cable_key][i]['object']['id'])
                        devices.append(dict(zip(device_keys, device_values)))
            config_context = SimpleNamespace(**dict(
                netbox_api.dcim.devices.get(
                    device_id).config_context))  # type: ignore
            roles = config_context.network_devices_roles
            roles.extend(config_context.user_devices_roles)
            for device in devices:
                device_roles.append(device['role'])
            logger.log_info('{} cable ID #{} between {}.'.format(event_type.upper(), cable_data['id'], device_names))  # type: ignore
            if set(device_roles).issubset(set(roles)):
                for device in devices:
                    if device['role'] == roles[0]:
                        device_intf_id = device['intf_id']
                get_device_interface = netbox_api.dcim.interfaces.get(device_intf_id)
                interface_name = convert_none_to_str(
                    get_device_interface.name if get_device_interface.name else None)  # type: ignore
                interface_mode_802_1Q = convert_none_to_str(
                    get_device_interface.mode.value if get_device_interface.mode else None)  # type: ignore
                global_id = get_device_interface.device.id  # type: ignore
                config_context = SimpleNamespace(**dict(netbox_api.dcim.devices.get(global_id).config_context))  # type: ignore
                logger.log_info(f'Connection between {device_roles[0]} and {device_roles[1]}, switch access interface ID: {device_intf_id}.')
                if get_device_interface.mgmt_only:  # type: ignore
                    comment = f'{interface_name} is management interface, no changes will be performed'
                    logger.log_info(comment)
                elif interface_mode_802_1Q in ['tagged', 'tagged-all']:
                    logger.log_info(f'Interface {interface_name} is mode {interface_mode_802_1Q}')
                else:
                    if event_type == "created" and get_device_interface is not None:
                        manage_connected_interfaces(get_device_interface, event='create', role=roles[0], config_context=config_context)
                    elif event_type == "deleted" and get_device_interface is not None:
                        manage_connected_interfaces(get_device_interface, event='delete', role=roles[0], config_context=config_context)
                    elif get_device_interface.enabled == False:  # type: ignore
                        logger.log_info('Interface {interface_name} was turned off before')
                        pass
                    elif event_type == "updated" and compare(pre_change_snapshot, post_change_snapshot) is not None:
                        change_config_intf(netbox_interface=get_device_interface, event='update', config_context=config_context)
                    else:
                        comment = f'No data for {event_type.lower()} {interface_name}'
                        logger.log_info(comment)
            else:
                comment = f'Devices must match the list of {roles}'
                logger.log_info(comment)
    except ValueError as ve:
        logger.log_error(f"ValueError occurred: {ve}")
    except KeyError as ke:
        logger.log_error(f"KeyError occurred: {ke}")
    finally:
        return Response(status=204)


def mng_int() -> Response:
    """
    This function manages interfaces. It processes requests in JSON format and
    performs various actions based on the request data. It logs any errors
    that occur during execution. The function takes no parameters. It returns
    a Flask Response object with an HTTP status code of 204.
    """
    try:
        if request.json:
            data = request.json['data']
            event_type = request.json['event']
            pre_change_snapshot = request.json['snapshots']['prechange']
            post_change_snapshot = request.json['snapshots']['postchange']
            intf_id = data['id']
            intf = netbox_api.dcim.interfaces.get(intf_id)
            intf_name = convert_none_to_str(intf.name)  # type: ignore
            device_role = convert_none_to_str(intf.device.device_role.slug)  # type: ignore
            intf_mode_802_1Q = convert_none_to_str(intf.mode.value if intf.mode else None)  # type: ignore
            config_context = SimpleNamespace(**dict(netbox_api.dcim.devices.get(global_id).config_context))
            network_devices_roles = convert_none_to_str(config_context.network_devices_roles)
            user_devices_roles = convert_none_to_str(config_context.user_devices_roles)

            logger.log_info(f"{event_type.upper()} {intf_name}.")
            if intf.mgmt_only:  # type: ignore
                comment = f'{intf_name} is management interface, no changes will be performed'
                logger.log_info(comment)
            elif compare(pre_change_snapshot, post_change_snapshot) is None:
                comment = f'No data for {event_type.lower()} {intf_name}'
                logger.log_info(comment)
            elif data['enabled'] is False and pre_change_snapshot['enabled'] is False:
                logger.log_warning(f'Interface {intf_name} was turned off before')
            elif device_role in network_devices_roles:
                if intf_mode_802_1Q in ['tagged', 'tagged-all']:
                    logger.log_info('Interface {} is mode {}'.format(intf_name, intf_mode_802_1Q))
                    change_config_intf(intf,
                                       event='update',
                                       netbox_config_context=config_context)
                else:
                    if data['enabled'] is False and pre_change_snapshot['enabled'] is True:
                        comment = f'Interface {intf_name} is disabled on the device'
                        logger.log_info(comment)
                        change_config_intf(intf,
                                           event='shutdown',
                                           netbox_config_context=config_context)
                    else:
                        change_config_intf(intf,
                                           event='update',
                                           netbox_config_context=config_context)
            elif device_role in user_devices_roles and intf is not None:
                manage_connected_interfaces(intf,
                                            event='update',
                                            role=device_role,
                                            netbox_config_context=config_context)
            else:
                logger.log_info(f'Device role is "{device_role}"')
    except ValueError as ve:
        logger.log_error(f"ValueError occurred: {ve}")
    except KeyError as ke:
        logger.log_error(f"KeyError occurred: {ke}")
    finally:
        return Response(status=204)
