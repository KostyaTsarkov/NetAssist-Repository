from typing import Tuple
from snmp_trap import SNMPTrap
from dataclasses import asdict
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
            trap = self._process_trap(req_pdu, p_mod, snmp_type)
            self.handle_SNMP_trap(trap)

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
            trap = SNMPTrap(
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
            trap = SNMPTrap(
                enterprise='',
                agent_address='',
                generic_trap='',
                specific_trap='',
                time_stamp='',
                var_binds=var_bind_list
            )

        return trap

    def handle_SNMP_trap(self, trap) -> None:
        """
        Обрабатывает SNMP-трап.

        Args:
            trap (dict): Словарь, содержащий информацию о трапе.
        """
        trap_dict = asdict(trap)
        if not self._is_valid_trap(trap_dict):
            self.logger.log_warning(f'Получена невалидная ловушка: {trap_dict}')
            return
        self.logger.log_info(f'Ловушка получена: {trap_dict}')
        varbind, interface = self._parse_SNMP_trap(trap_dict)
        self.database.add_interface(interface.to_dict())
        # self.logger.log_info(f"Ловушка обработана: {varbind.oid} = {varbind.value}")
        relay = SNMPTrapRelay(logger=self.logger)
        relay.relay_SNMP_trap(varbind)

    def _parse_SNMP_trap(self, trap_dict: dict) -> Tuple[SNMPVarBind,
                                                    SNMPInterface]:
        """
        Разбирает словарь, содержащий информацию о трапе.

        Args:
            trap_dict (dict): Словарь, содержащий информацию о трапе.

        Returns:
            Tuple[SNMPVarBind, SNMPInterface]: Кортеж из объекта SNMPVarBind и
            объекта SNMPInterface.
        """
        # varbind = []
        varbind = {}
        for dic in trap_dict.get('var_binds'):
            oid = dic.get('oid')
            if '1.3.6.1.4.1.9.2.2.1.1.20.' in oid:
                # varbind.append(dic.get('value'))
                varbind['if_state'] = dic.get('value')
                # varbind.append(result_dict)
            if '1.3.6.1.2.1.2.2.1.2.' in oid:
                # varbind.append(dic.get('value'))
                varbind['if_name'] = dic.get('value')
                # varbind.append(result_dict)
            if '1.3.6.1.2.1.2.2.1.1.' in oid:
                # varbind.append(dic.get('value'))
                varbind['if_index'] = dic.get('value')
                # varbind.append(result_dict)
                
        """ if_index = trap_dict.get('if_index')
        if_admin_status = trap_dict.get('if_admin_status')
        if_oper_status = trap_dict.get('if_oper_status')
        if_in_errors = trap_dict.get('if_in_errors')
        if_out_errors = trap_dict.get('if_out_errors')
        if_in_discards = trap_dict.get('if_in_discards')
        if_out_discards = trap_dict.get('if_out_discards')

        interface = SNMPInterface(if_admin_status, if_oper_status,
                                  if_in_errors, if_out_errors,
                                  if_in_discards, if_out_discards)
        interface.if_index = if_index """
        interface = SNMPInterface(ip_address='10.30.1.105',
                                  community=str(self.snmp_community),
                                  if_index=int(varbind.get('if_index')),
                                  version=2)

        return varbind, interface

    def _is_valid_trap(self, trap_dict: dict) -> bool:
        """
        Проверяет, является ли полученный трап валидным.

        Аргументы:
            trap_dict: Словарь, представляющий трап.

        Возвращает:
            True, если трап является валидным, False в противном случае.
        """
        for dic in trap_dict.get('var_binds'):
            oid = dic.get('oid')
            value = dic.get('value')
            if not oid or not value:
                return False
        return True
