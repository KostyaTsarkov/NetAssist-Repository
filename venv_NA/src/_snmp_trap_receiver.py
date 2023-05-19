import json
from pysnmp.carrier.asyncore.dispatch import AsyncoreDispatcher
from pysnmp.carrier.asyncore.dgram import udp


snmp_sender = '0.0.0.0'
snmp_host = "127.0.0.1"
snmp_port = 5001
dispatcher = AsyncoreDispatcher()
transport = udp.UdpSocketTransport().openServerMode((snmp_host, snmp_port))


def handle_trap(_, __, ___, pdu):
    # извлекаем данные из PDU
    trap_oid = str(pdu[3][0][0])
    trap_value = str(pdu[3][0][1])
    trap_dict = {"oid": trap_oid, "value": trap_value}
    trap_json = json.dumps(trap_dict)


""" def myRecvCb(dispatcher, transport, snmp_sender, wholeMsg):
    print(wholeMsg) """


dispatcher.registerRecvCbFun(handle_trap)
dispatcher.registerTransport(udp.domainName, transport)
dispatcher.jobStarted(1)
dispatcher.runDispatcher()
