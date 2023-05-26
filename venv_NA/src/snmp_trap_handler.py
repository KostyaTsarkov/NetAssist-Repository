from datetime import datetime
import pytz
from typing import Any, Tuple
from snmp_trap import SNMPTrap
from dataclasses import asdict
from snmp_var_bind import SNMPVarBind
from snmp_interface import SNMPInterface
from snmp_trap_relay import SNMPTrapRelay
from pyasn1.codec.ber import decoder
from pysnmp.proto import api
from config import config_data
from logger import Logger

logger = Logger('app.log')


class SNMPTrapHandler:
    """
    Класс для обработки SNMP-трапов.

    Атрибуты:
        snmp_community (str): Коммьюнити для доступа к SNMP-агенту.
        database (Database): Объект класса Database для работы с базой данных.
        logger (Logger): Объект класса Logger для логирования сообщений.
    """

    def __init__(self,
                 snmp_community: str,
                 database,
                 logger) -> None:
        """
        Initializes the class instance with given snmp community, database and logger.

        :param snmp_community: A string representing the snmp community.
        :param database: An object representing the database.
        :param logger: An object representing the logger.
        :return: None
        """

        self.snmp_community = snmp_community
        self.database = database
        self.logger = logger

    def whole_SNMP_trap(self,
                        dispatcher,
                        transport,
                        snmp_sender,
                        whole_message) -> None:
        """
        This function handles a SNMP trap message by extracting the SNMP community from the message,
        processing the trap, and handling it. It takes in the dispatcher, transport, snmp_sender,
        and the whole_message as parameters. It returns None.

        Parameters:
            dispatcher (Any): The dispatcher that received the message.
            transport (Any): The transport the message was received on.
            snmp_sender (str): The sender of the SNMP trap.
            whole_message (bytes): The full SNMP trap message.

        Return:
            None
        """
        self.logger.log_info(f'Received SNMP trap from {transport}:{snmp_sender}')
        trap_date = datetime.now(pytz.utc)
        snmp_type, p_mod = self._handle_SNMP_version(whole_message)
        if not p_mod:
            return
        req_message, whole_message = decoder.decode(
            whole_message, asn1Spec=p_mod.Message()
        )
        snmp_community = self._extract_snmp_community(req_message, p_mod)
        if snmp_community is None:
            return
        self.logger.log_info(f'Notification message from {transport}:{snmp_sender}')
        req_pdu = p_mod.apiMessage.getPDU(req_message)
        if not req_pdu.isSameTypeWith(p_mod.TrapPDU()):
            return
        trap = self._process_trap(req_pdu, p_mod, snmp_type)
        self.handle_SNMP_trap(trap,
                              snmp_sender,
                              trap_date.strftime("%m/%d/%Y, %H:%M:%S"))

    def _extract_snmp_community(self,
                                req_message,
                                p_mod) -> str:
        """
        Extracts the SNMP community from the request message and compares it to the expected
        community for the device. If they match, return the community. Otherwise, log a warning
        and return None.

        :param req_message: A request message to extract the SNMP community from.
        :type req_message: unknown
        :param parsed_module: A parsed module object.
        :type parsed_module: unknown
        :return: The SNMP community if it matches the expected community, otherwise None.
        :rtype: str or None
        """
        req_community = p_mod.apiMessage.getCommunity(req_message)._value.decode('utf-8')
        if req_community == self.snmp_community:
            return req_community
        self.logger.log_warning(f'Wrong SNMP community {req_community}')
        return None

    def _handle_SNMP_version(self,
                             whole_message) -> Tuple[int, Any]:
        """
        This function handles the SNMP version in the given message.

        :param whole_message: The SNMP message to handle the version for.
        :type whole_message: bytes
        :return: A tuple containing the SNMP version as an integer and the corresponding protocol module.
        :rtype: tuple[int, Any]
        """
        snmp_type = int(api.decodeMessageVersion(whole_message))
        p_mod = api.protoModules.get(snmp_type)
        if not p_mod:
            self.logger.log_warning(f'Unsupported SNMP version {snmp_type}')
            return snmp_type, None
        return snmp_type, p_mod

    def _process_snmpv1_trap(self,
                             req_pdu,
                             p_mod) -> SNMPTrap:
        """
        Processes an SNMPv1 trap message and returns a SNMPTrap object containing the specified information.

        :param req_pdu: The PDU object containing the SNMPv1 trap message.
        :type req_pdu: PDU

        :param p_mod: The PySNMP module containing the API for accessing the SNMP trap information.
        :type p_mod: PySNMP module

        :return: A SNMPTrap object containing the enterprise, agent address, generic trap, specific trap, time stamp, and variable binds of the SNMPv1 trap message.
        :rtype: SNMPTrap
        """
        return SNMPTrap(
            enterprise=str(p_mod.apiTrapPDU.getEnterprise(req_pdu)),
            agent_address=str(p_mod.apiTrapPDU.getAgentAddr(req_pdu)),
            generic_trap=str(p_mod.apiTrapPDU.getGenericTrap(req_pdu)),
            specific_trap=str(p_mod.apiTrapPDU.getSpecificTrap(req_pdu)),
            time_stamp=str(p_mod.apiTrapPDU.getTimeStamp(req_pdu)),
            var_binds=[SNMPVarBind(str(var_bind[0]), str(var_bind[1]))for var_bind in p_mod.apiTrapPDU.getVarBindList(req_pdu)]
        )

    def _process_snmpv2c_trap(self,
                              req_pdu,
                              p_mod) -> SNMPTrap:
        """
        Processes an SNMPv2c trap by extracting the variable bindings from the request PDU and
        returning an SNMPTrap object with the relevant information.

        Args:
            req_pdu (object): The request PDU object containing the variable bindings.
            p_mod (object): The PDU module object used to extract the variable bindings.

        Returns:
            SNMPTrap: An SNMPTrap object with the following attributes:
                - enterprise (str): The enterprise ID of the trap.
                - agent_address (str): The IP address of the agent that generated the trap.
                - generic_trap (str): The generic trap type of the trap.
                - specific_trap (str): The specific trap type of the trap.
                - time_stamp (str): The timestamp when the trap was generated.
                - var_binds (list): A list of dictionaries representing the variable bindings
                  extracted from the request PDU. Each dictionary has two keys:
                    - oid (str): The OID of the variable binding.
                    - value (str): The value of the variable binding.
        """
        var_binds = p_mod.apiPDU.getVarBinds(req_pdu)
        var_bind_list = []
        for oid, val in var_binds:
            var_bind_list.append({"oid": oid.prettyPrint(),
                                  "value": val.prettyPrint()})
        return SNMPTrap(
            enterprise='',
            agent_address='',
            generic_trap='',
            specific_trap='',
            time_stamp='',
            var_binds=var_bind_list
        )

    def _process_trap(self,
                      req_pdu,
                      p_mod,
                      snmp_type) -> Any:
        """
        Processes a trap using either SNMPv1 or SNMPv2c protocol based on the given snmp_type.

        :param req_pdu: The request Protocol Data Unit (PDU) that is being processed
        :type req_pdu: ProtocolDataUnit

        :param p_mod: The module that contains the enterprise-specific information for the trap
        :type p_mod: ObjectIdentity

        :param snmp_type: The SNMP protocol version of the trap. Can be either api.protoVersion1 or any other value for SNMPv2c
        :type snmp_type: int

        :return: The result of the trap processing. Either the result of _process_snmpv1_trap or _process_snmpv2c_trap based on snmp_type value
        :rtype: Any
        """
        if snmp_type == api.protoVersion1:
            return self._process_snmpv1_trap(req_pdu, p_mod)
        else:
            return self._process_snmpv2c_trap(req_pdu, p_mod)

    def handle_SNMP_trap(self,
                         trap,
                         snmp_sender,
                         trap_date_str) -> None:
        """
        Handles a received SNMP trap by parsing its information and relaying it to the
        appropriate parties.

        :param trap: The SNMP trap to be handled.
        :type trap: any
        :param snmp_sender: The IP address of the sender of the SNMP trap.
        :type snmp_sender: str
        :param trap_date_str: The string representation of the date when the trap was received.
        :type trap_date_str: str
        :return: None
        :rtype: None
        """

        ip_address = snmp_sender[0]
        trap_dict = asdict(trap)
        if not self._is_valid_trap(trap_dict):
            self.logger.log_warning(f'Received a non-invalid trap: {trap_dict}')
            return
        self.logger.log_info(f'Trap received: {trap_dict}')
        varbind, interface = self._parse_SNMP_trap(trap_dict, ip_address)
        varbind['ip_address'] = ip_address
        varbind['trap_date'] = trap_date_str
        self.database.add_interface(interface)
        relay = SNMPTrapRelay(logger=self.logger)
        relay.relay_SNMP_trap(varbind)

    def _parse_SNMP_trap(self,
                         trap_dict: dict,
                         ip_address: str) -> Tuple[SNMPVarBind,
                                                   SNMPInterface]:
        """
        Parses an SNMP trap dictionary and returns a tuple containing the varbind and SNMPInterface objects.

        :param trap_dict: A dictionary containing SNMP trap information.
        :type trap_dict: dict
        :param ip_address: The IP address of the interface.
        :type ip_address: str
        :return: A tuple containing the SNMPVarBind and SNMPInterface objects.
        :rtype: Tuple[SNMPVarBind, SNMPInterface]
        """
        IF_STATE_OID = '1.3.6.1.4.1.9.2.2.1.1.20.'
        IF_NAME_OID = '1.3.6.1.2.1.2.2.1.2.'
        IF_INDEX_OID = '1.3.6.1.2.1.2.2.1.1.'

        varbind = {}
        if_index = None

        for dic in trap_dict.get('var_binds'):
            oid = dic.get('oid')
            if IF_STATE_OID in oid:
                varbind['if_state'] = dic.get('value')
            if IF_NAME_OID in oid:
                varbind['if_name'] = dic.get('value')
            if IF_INDEX_OID in oid:
                if_index = int(dic.get('value'))
                varbind['if_index'] = if_index

        interface = SNMPInterface(ip_address=ip_address,
                                  community=str(self.snmp_community),
                                  if_index=varbind.get('if_index'),
                                  version=int(config_data['snmp_version']))

        return varbind, interface

    def _is_valid_trap(self,
                       trap_dict: dict) -> bool:
        """
        Validates if the given trap dictionary is valid by checking if every 'var_binds' element has an 'oid' and 'value' attribute.

        :param trap_dict: A dictionary representing a trap with 'var_binds' attribute.
        :type trap_dict: dict

        :return: True if all 'var_binds' elements have 'oid' and 'value' attribute, False otherwise.
        :rtype: bool
        """
        for dic in trap_dict.get('var_binds'):
            oid = dic.get('oid')
            value = dic.get('value')
            if not oid or not value:
                return False
        return True
