from pysnmp.carrier.asyncore.dispatch import AsyncoreDispatcher
from pysnmp.carrier.asyncore.dgram import udp
from pysnmp.smi import builder, view
from pysnmp.entity import engine, config
from snmp_trap_handler import SNMPTrapHandler
import config as config_data


class SNMPTrapReceiver:
    def __init__(self):
        self.listen_address = config_data["listen_address"]
        self.community = config_data["community"]
        self.snmp_version = config_data["snmp_version"]
        self.builder = builder.MibBuilder()
        self.view_controller = view.MibViewController(self.builder)
        self.snmp_engine = None
        self.transport_dispatcher = None

    def start(self):
        self.snmp_engine = engine.SnmpEngine()
        self.transport_dispatcher = AsyncoreDispatcher()
        transport = udp.UdpSocketTransport().openServerMode((self.listen_address, 162))
        self.transport_dispatcher.registerTransport(udp.domainName, transport)
        self.transport_dispatcher.jobStarted(1)
        self.snmp_engine.registerTransportDispatcher(self.transport_dispatcher)

        if self.snmp_version == 1:
            config.addV1System(self.snmp_engine, 'my-area', self.community)
        elif self.snmp_version == 2 or self.snmp_version == '2c':
            config.addV2Community(self.snmp_engine, 'my-area', self.community)
        else:
            raise ValueError('Unsupported SNMP version')
        config.addVacmUser(self.snmp_engine, 2, 'my-area', 'noAuthNoPriv', (), (), ())

        self.snmp_engine.registerRecvCbFun(lambda *x: handler.handle_trap(*x))
        self.snmp_engine.transportDispatcher.runDispatcher()

    def stop(self):
        self.snmp_engine.transportDispatcher.closeDispatcher()


handler = SNMPTrapHandler()
receiver = SNMPTrapReceiver()
receiver.start()
