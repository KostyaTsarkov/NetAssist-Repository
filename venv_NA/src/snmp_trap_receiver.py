from pysnmp.carrier.asyncore.dispatch import AsyncoreDispatcher
from pysnmp.carrier.asyncore.dgram import udp
from pysnmp.smi import builder, view
from snmp_trap_handler import SNMPTrapHandler
from config import config_data
from database import Database
from logger import Logger


class SNMPTrapReceiver:
    def __init__(self):
        self.listen_address = config_data["listen_address"]
        self.snmp_port = config_data["snmp_port"]
        self.community = config_data["community"]
        self.snmp_version = config_data["snmp_version"]
        self.database = Database(config_data["database"])
        self.logger = Logger(config_data["logger"])
        self.builder = builder.MibBuilder()
        self.view_controller = view.MibViewController(self.builder)
        self.snmp_engine = None
        self.transport_dispatcher = None

    def start(self):
        """
        Initializes the AsyncoreDispatcher and registers 
        the SNMPTrapHandler to handle incoming SNMP traps.
        :return: None
        """
        self.dispatcher = AsyncoreDispatcher()
        transport = udp.UdpSocketTransport().openServerMode(
            (self.listen_address, self.snmp_port)
        )
        handler = SNMPTrapHandler(self.community, self.database, self.logger)
        self.dispatcher.registerRecvCbFun(lambda *x: handler.whole_SNMP_trap(*x))
        self.dispatcher.registerTransport(udp.domainName, transport)
        self.dispatcher.jobStarted(1)
        self.dispatcher.runDispatcher()

    def stop(self):
        """
        Stop the process initiated by the dispatcher.
        :return: None
        """
        self.dispatcher.closeDispatcher()


receiver = SNMPTrapReceiver()
receiver.start()
