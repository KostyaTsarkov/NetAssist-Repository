from typing import Tuple
from snmp_trap import SNMPTrap
from snmp_var_bind import SNMPVarBind
from snmp_interface import SNMPInterface
from snmp_trap_relay import SNMPTrapRelay
from pyasn1.codec.ber import decoder
from pysnmp.proto import api


class SNMPTrapHandler:
    """
    Класс для обработки SNMP-трапов.

    Атрибуты:
        snmp_community (str): Коммьюнити для доступа к SNMP-агенту.
        database (Database): Объект класса Database для работы с базой данных.
        logger (Logger): Объект класса Logger для логирования сообщений.
    """

    def __init__(self, snmp_community: str,
                 database,
                 logger) -> None:
        """
        Инициализирует объект SNMPTrapHandler.

        Аргументы:
            snmp_community: Коммьюнити для доступа к SNMP-агенту.
            database: Объект класса Database для работы с базой данных.
            logger: Объект класса Logger для логирования сообщений.
        """
        self.snmp_community = snmp_community
        self.database = database
        self.logger = logger

    def whole_SNMP_trap(self, dispatcher, transport,
                        snmp_sender, whole_message) -> None:
        snmp_type, p_mod = self._handle_SNMP_version(whole_message)
        if not p_mod:
            return
        req_message, whole_message = decoder.decode(
            whole_message, asn1Spec=p_mod.Message(),
        )
        self.logger.log_info(f'Notification message from {transport}:{snmp_sender}')
        req_pdu = p_mod.apiMessage.getPDU(req_message)
        if req_pdu.isSameTypeWith(p_mod.TrapPDU()):
            trap_dict = self._process_trap(req_pdu, p_mod, snmp_type)
            self.handle_SNMP_trap(trap_dict)

    def _handle_SNMP_version(self, whole_message):
        snmp_type = int(api.decodeMessageVersion(whole_message))
        if snmp_type in api.protoModules:
            p_mod = api.protoModules[snmp_type]
        else:
            self.logger.warning(f'Unsupported SNMP version {snmp_type}')
            return snmp_type, None
        return snmp_type, p_mod

    def _process_trap(self, req_pdu, p_mod, snmp_type):
        if snmp_type == api.protoVersion1:
            trap_dict = SNMPTrap(
                enterprise=str(p_mod.apiTrapPDU.getEnterprise(req_pdu)),
                agent_address=str(p_mod.apiTrapPDU.getAgentAddr(req_pdu)),
                generic_trap=str(p_mod.apiTrapPDU.getGenericTrap(req_pdu)),
                specific_trap=str(p_mod.apiTrapPDU.getSpecificTrap(req_pdu)),
                time_stamp=str(p_mod.apiTrapPDU.getTimeStamp(req_pdu)),
                var_binds=[SNMPVarBind(str(var_bind[0]), str(var_bind[1]))for var_bind in p_mod.apiTrapPDU.getVarBindList(req_pdu)]
            )
        else:
            var_binds = p_mod.apiPDU.getVarBinds(req_pdu)
            var_bind_list = []
            for oid, val in var_binds:
                var_bind_list.append({"oid": oid.prettyPrint(),
                                      "value": val.prettyPrint()})
            trap_dict = SNMPTrap(
                enterprise='',
                agent_address='',
                generic_trap='',
                specific_trap='',
                time_stamp='',
                var_binds=var_bind_list
            )

        return trap_dict

    def handle_SNMP_trap(self, trap_dict: dict) -> None:
        """
        Обрабатывает SNMP-трап.

        Args:
            trap (dict): Словарь, содержащий информацию о трапе.
        """
        if not self._is_valid_trap(trap_dict):
            self.logger.log_warning(f'Получена невалидная ловушка: {trap_dict}')
            return
        self.logger.log_info(f'Ловушка получена: {trap_dict}')
        varbind, interface = self._parse_SNMP_trap(trap_dict)
        self.database.add_interface(interface.to_dict())
        self.logger.log_info
        (f"Ловушка обработана: {varbind.oid} = {varbind.value}")
        relay = SNMPTrapRelay(logger=self.logger)
        relay.relay_SNMP_trap(trap_dict)

    def _parse_SNMP_trap(self, trap: dict) -> Tuple[SNMPVarBind,
                                                    SNMPInterface]:
        """
        Разбирает словарь, содержащий информацию о трапе.

        Args:
            trap (dict): Словарь, содержащий информацию о трапе.

        Returns:
            Tuple[SNMPVarBind, SNMPInterface]: Кортеж из объекта SNMPVarBind и
            объекта SNMPInterface.
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

    def _is_valid_trap(self, trap_dict: dict) -> bool:
        """
        Проверяет, является ли полученный трап валидным.

        Аргументы:
            trap_dict: Словарь, представляющий трап.

        Возвращает:
            True, если трап является валидным, False в противном случае.
        """
        if not trap_dict.get('oid') or not trap_dict.get('value'):
            self.logger.warning(f"Получена недопустимая ловушка: {trap_dict}")
            return False
        return True
