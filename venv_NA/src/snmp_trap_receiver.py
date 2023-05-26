from queue import Queue
import threading
from pysnmp.carrier.asyncore.dispatch import AsyncoreDispatcher
from pysnmp.carrier.asyncore.dgram import udp
from pysnmp.smi import builder, view
from snmp_trap_handler import SNMPTrapHandler
from database import Database
from logger import Logger
from config import config_data

logger = Logger('app.log')


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

    def __init__(self,
                 config_data: dict) -> None:
        """
        Initializes the SNMP agent application using the provided configuration data.

        Args:
            config_data (dict): A dictionary containing the configuration data for the SNMP agent.

        Returns:
            None
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

    def start(self, num_threads: int) -> None:
        """
        The start method initializes a UDP socket transport in server mode to listen on the given
        listen address and SNMP port. It creates an SNMP trap handler object with the given 
        community, database, and logger. It registers the whole_SNMP_trap method of the handler as
        the callback function for received SNMP traps. It registers the UDP transport with the 
        dispatcher and starts the dispatcher to receive SNMP traps. If any exception is raised, it
        logs the error and stops the receiver. This method does not take any parameters and does not
        return anything.
        """
        try:
            self.logger = Logger(config_data["logger"])
            transport = udp.UdpSocketTransport().openServerMode(
                (self.listen_address, self.snmp_port)
            )
            handler = SNMPTrapHandler(self.community,
                                      self.database,
                                      self.logger)
            trap_queue = Queue()
            for i in range(num_threads):
                t = threading.Thread(target=self.worker, args=(trap_queue,
                                                               handler))
                t.daemon = True
                t.start()
            self.dispatcher.registerRecvCbFun(lambda *x: trap_queue.put(x))
            self.dispatcher.registerTransport(udp.domainName, transport)
            self.dispatcher.jobStarted(1)
            self.dispatcher.runDispatcher()
        except Exception as e:
            self.logger.log_error(f"Error starting SNMP trap receiver: {e}")
            self.stop()

    def stop(self) -> None:
        """
        Stops the function and closes the dispatcher.
        Does not take any parameters.
        Returns None.
        """
        self.logger.log_info("Stopping SNMP trap receiver.")
        self.dispatcher.closeDispatcher()

    def worker(self, trap_queue, handler):
        while True:
            trap = trap_queue.get()
            handler.whole_SNMP_trap(*trap)
            trap_queue.task_done()

    def __del__(self):
        self.stop()


# receiver = SNMPTrapReceiver(config_data)
# receiver.start(num_threads=5)
# receiver.stop()
