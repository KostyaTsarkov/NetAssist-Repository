from pysnmp.carrier.asyncore.dispatch import AsyncoreDispatcher
from pysnmp.carrier.asyncore.dgram import udp
from pysnmp.smi import builder, view
from snmp_trap_handler import SNMPTrapHandler
from database import Database
from logger import Logger
from config import config_data


class SNMPTrapReceiver:
    """
    Класс для получения SNMP-ловушек.

    Атрибуты:
    ----------
    mib_builder: pysnmp.smi.builder.MibBuilder
        Экземпляр класса MibBuilder, используемый для компиляции MIB.
    mib_view_controller: pysnmp.smi.view.MibViewController
        Экземпляр класса MibViewController, используемый для управления
        объектами MIB.
    transport_dispatcher: None
        Экземпляр класса transport dispatcher.
    listen_address: str
        IP-адрес, на котором происходит прослушивание.
    snmp_port: int
        UDP-порт, на котором происходит прослушивание.
    community: str
        Строка community.
    snmp_version: int
        Версия SNMP.
    database: Database
        Экземпляр класса Database.
    logger: Logger
        Экземпляр класса Logger.
    """
    def __init__(self, config_data: dict) -> None:
        """
        Инициализирует экземпляр класса с переменными для MIB builder,
        MIB view controller, SNMP engine и transport dispatcher.
        """
        self.mib_builder = builder.MibBuilder()
        self.mib_view_controller = view.MibViewController(self.mib_builder)
        self.dispatcher = AsyncoreDispatcher()
        try:
            self.logger = Logger(config_data["logger"])
            self.listen_address = config_data["listen_address"]
            self.snmp_port = config_data["snmp_port"]
            self.community = config_data["community"]
            self.snmp_version = config_data["snmp_version"]
            self.database = Database(config_data["database"])
        except KeyError as e:
            raise ValueError("Отсутствуют данные конфигурации") from e

    def start(self) -> None:
        """
        Инициализирует AsyncoreDispatcher и регистрирует SNMPTrapHandler
        для обработки входящих SNMP-ловушек.

        :return: None
        """
        try:
            self.logger = Logger(config_data["logger"])
            transport = udp.UdpSocketTransport().openServerMode(
                (self.listen_address, self.snmp_port)
            )
            handler = SNMPTrapHandler(self.community, self.database, self.logger)
            self.dispatcher.registerRecvCbFun(lambda *x: handler.whole_SNMP_trap(*x))
            self.dispatcher.registerTransport(udp.domainName, transport)
            self.dispatcher.jobStarted(1)
            self.dispatcher.runDispatcher()
        except Exception as e:
            self.logger.log_error(f"Ошибка при запуске SNMPTrapReceiver: {e}")
            self.stop()

    def stop(self) -> None:
        """
        Останавливает процесс, инициированный диспетчером.

        :return: None
        """
        with self.dispatcher:
            self.dispatcher.closeDispatcher()

    def __del__(self):
        self.stop()


receiver = SNMPTrapReceiver(config_data)
receiver.start()
# receiver.stop()
