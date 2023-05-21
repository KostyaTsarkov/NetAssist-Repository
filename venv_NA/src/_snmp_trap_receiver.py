import json
from pysnmp.carrier.asyncore.dispatch import AsyncoreDispatcher
from pysnmp.carrier.asyncore.dgram import udp
from pyasn1.codec.ber import decoder
from pysnmp.proto import api


snmp_sender = '0.0.0.0'
snmp_host = "127.0.0.1"
snmp_port = 5001
dispatcher = AsyncoreDispatcher()
transport = udp.UdpSocketTransport().openServerMode((snmp_host, snmp_port))


""" def handle_trap(_, __, ___, pdu):
    # извлекаем данные из PDU
    trap_oid = str(pdu[3][0][0])
    trap_value = str(pdu[3][0][1])
    trap_dict = {"oid": trap_oid, "value": trap_value}
    trap_json = json.dumps(trap_dict) """


def myRecvCb(dispatcher, transport, snmp_sender, wholeMsg):
    
    trap_dict = dict()
    while wholeMsg:
        msgVer = int(api.decodeMessageVersion(wholeMsg))
        if msgVer in api.protoModules:
            pMod = api.protoModules[msgVer]
        else:
            print('Unsupported SNMP version %s' % msgVer)
            return
        reqMsg, wholeMsg = decoder.decode(
            wholeMsg, asn1Spec=pMod.Message(),
        )
        print('Notification message from %s:%s: ' % (
            transport, snmp_sender
        )
              )
        reqPDU = pMod.apiMessage.getPDU(reqMsg)
        if reqPDU.isSameTypeWith(pMod.TrapPDU()):
            if msgVer == api.protoVersion1:
                print('Enterprise: %s' % (pMod.apiTrapPDU.getEnterprise(reqPDU).prettyPrint()))
                print('Agent Address: %s' % (pMod.apiTrapPDU.getAgentAddr(reqPDU).prettyPrint()))
                print('Generic Trap: %s' % (pMod.apiTrapPDU.getGenericTrap(reqPDU).prettyPrint()))
                print('Specific Trap: %s' % (pMod.apiTrapPDU.getSpecificTrap(reqPDU).prettyPrint()))
                print('Uptime: %s' % (pMod.apiTrapPDU.getTimeStamp(reqPDU).prettyPrint()))
                varBinds = pMod.apiTrapPDU.getVarBindList(reqPDU)
            else:
                varBinds = pMod.apiPDU.getVarBinds(reqPDU)
                for oid, val in varBinds:
                    #print('%s = %s' % (oid.prettyPrint(), val.prettyPrint()))
                    trap_dict = {"oid": oid.prettyPrint(), "value": val.prettyPrint()}
                    trap_json = json.dumps(trap_dict)
                print(trap_json)
    return wholeMsg


dispatcher.registerRecvCbFun(myRecvCb)
dispatcher.registerTransport(udp.domainName, transport)
dispatcher.jobStarted(1)
dispatcher.runDispatcher()
