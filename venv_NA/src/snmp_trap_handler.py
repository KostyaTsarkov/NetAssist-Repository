from typing import Tuple
from snmp_var_bind import SNMPVarBind
from snmp_interface import SNMPInterface
from config import config_data


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
        self.community = config_data["community"]
        self.database = config_data["database"]
        self.logger = config_data["logger"]
        #self.logger.setLevel(config_data["log_level"])

    def handle_SNMP_trap(self, trap: dict) -> None:
        """Обрабатывает SNMP-трап.

        Args:
            trap (dict): Словарь, содержащий информацию о трапе.
        """
        if 'oid' in trap and 'value' in trap:
            varbind, interface = self.parse_SNMP_trap(trap)
            print(f"Handling trap: varbind = {varbind.oid}, interface = {interface.if_admin_status}")
            self.database.add_interface(interface.to_dict())
            self.logger.log_info(f"Trap handled: {varbind.oid} = {varbind.value}")
        else:
            self.logger.warning(f"Invalid trap received: {trap}")

    def parse_SNMP_trap(self, trap: dict) -> Tuple[SNMPVarBind, SNMPInterface]:
        """Разбирает словарь, содержащий информацию о трапе.

        Args:
            trap (dict): Словарь, содержащий информацию о трапе.

        Returns:
            Tuple[SNMPVarBind, SNMPInterface]: Кортеж из объекта SNMPVarBind и объекта SNMPInterface.
        """
        varbind_oid = trap.get('varbind_oid')
        varbind_value = trap.get('varbind_value')
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
