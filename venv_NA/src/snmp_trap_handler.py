from typing import Tuple
from snmp_var_bind import SNMPVarBind
from snmp_interface import SNMPInterface
from snmp_trap_relay import SNMPTrapRelay
from pyasn1.codec.ber import decoder
from pysnmp.proto import api
import json


class SNMPTrapHandler:
    """Класс для обработки SNMP-трапов.

    Attributes:
        community (str): Коммьюнити для доступа к SNMP-агенту.
        database (Database): Объект класса Database для работы с базой данных.
        logger (Logger): Объект класса Logger для логирования сообщений.
    """

    def __init__(self, community, database, logger) -> None:
        """Инициализирует объект SNMPTrapHandler.

        Args:
            community (str): Коммьюнити для доступа к SNMP-агенту.
            database (Database): Объект класса Database для работы с базой данных.
            logger (Logger): Объект класса Logger для логирования сообщений.
        """
        self.community = community
        self.database = database
        self.logger = logger

    def whole_SNMP_trap(self, dispatcher, transport, snmp_sender, whole_message):
        """
        Эта функция получает целое сообщение SNMP trap и декодирует его,
        чтобы извлечь соответствующую информацию.

        Args:
            dispatcher: Экземпляр класса dispatcher.
            transport: Экземпляр класса transport.
            snmp_sender: Экземпляр класса SNMP sender.
            whole_message: Строка, представляющая целое сообщение SNMP trap.

        Returns:
            Строка JSON, представляющая извлеченную информацию SNMP trap.
        """
        trap_dict = dict()
        while whole_message:
            snmp_type = int(api.decodeMessageVersion(whole_message))
            if snmp_type in api.protoModules:
                p_mod = api.protoModules[snmp_type]
            else:
                print(f'Unsupported SNMP version {snmp_type}')
                return
            req_message, whole_message = decoder.decode(
                whole_message, asn1Spec=p_mod.Message(),
            )
            self.logger.log_info(f'Notification message from {transport}:{snmp_sender}')
            req_pdu = p_mod.apiMessage.getPDU(req_message)
            if req_pdu.isSameTypeWith(p_mod.TrapPDU()):
                if snmp_type == api.protoVersion1:
                    self.logger.log_info(f'Enterprise: {p_mod.apiTrapPDU.getEnterprise(req_pdu).prettyPrint()}')
                    self.logger.log_info(f'Agent Address: {p_mod.apiTrapPDU.getAgentAddr(req_pdu).prettyPrint()}')
                    self.logger.log_info(f'Generic Trap: {p_mod.apiTrapPDU.getGenericTrap(req_pdu).prettyPrint()}')
                    self.logger.log_info(f'Specific Trap: {p_mod.apiTrapPDU.getSpecificTrap(req_pdu).prettyPrint()}')
                    self.logger.log_info(f'Uptime: {p_mod.apiTrapPDU.getTimeStamp(req_pdu).prettyPrint()}')
                    var_binds = p_mod.apiTrapPDU.getVarBindList(req_pdu)
                else:
                    var_binds = p_mod.apiPDU.getVarBinds(req_pdu)
                    for oid, val in var_binds:
                        trap_dict = {"oid": oid.prettyPrint(), "value": val.prettyPrint()}
                        #trap_json = json.dumps(trap_dict)
                #print(trap_json)
                #self.handle_SNMP_trap(trap_dict)
                relay = SNMPTrapRelay()
                relay.relay_SNMP_trap(trap_dict)
                #return trap_json

    def handle_SNMP_trap(self, trap: dict) -> None:
        """
        Обрабатывает SNMP-трап.

        Args:
            trap (dict): Словарь, содержащий информацию о трапе.
        """
        if trap.get('oid') and trap.get('value'):
            varbind, interface = self.parse_SNMP_trap(trap)
            print(f"Handling trap: varbind = {varbind.oid}, interface = {interface.if_admin_status}")
            self.database.add_interface(interface.to_dict())
            self.logger.log_info(f"Trap handled: {varbind.oid} = {varbind.value}")
        else:
            self.logger.warning(f"Invalid trap received: {trap}")

    def parse_SNMP_trap(self, trap: dict) -> Tuple[SNMPVarBind, SNMPInterface]:
        """
        Разбирает словарь, содержащий информацию о трапе.

        Args:
            trap (dict): Словарь, содержащий информацию о трапе.

        Returns:
            Tuple[SNMPVarBind, SNMPInterface]: Кортеж из объекта SNMPVarBind и объекта SNMPInterface.
        """
        varbind_oid = trap.get('oid')
        varbind_value = trap.get('value')
        varbind = SNMPVarBind(varbind_oid, varbind_value)

        if_index = trap.get('if_index')
        if_admin_status = trap.get('if_admin_status')
        if_oper_status = trap.get('if_oper_status')
        if_in_errors = trap.get('if_in_errors')
        if_out_errors = trap.get('if_out_errors')
        if_in_discards = trap.get('if_in_discards')
        if_out_discards = trap.get('if_out_discards')

        interface = SNMPInterface(if_admin_status, if_oper_status,
                                  if_in_errors, if_out_errors,
                                  if_in_discards, if_out_discards)
        interface.if_index = if_index

        return varbind, interface
