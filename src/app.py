from flask import Flask, request, jsonify
import requests
from pysnmp.hlapi import (
    CommunityData,
    SnmpEngine,
    UdpTransportTarget,
    ContextData,
    ObjectType,
    ObjectIdentity,
    nextCmd
)
import json

from snmp_trap_handler import SNMPTrapHandler
from database import Database
from logger import Logger

app = Flask(__name__)
database = Database('interfaces.db')
logger = Logger('app.log')

# создаем объект SNMPTrapHandler
trap_handler = SNMPTrapHandler('public', database, logger)

# адрес и порт Flask-приложения
flask_host = 'localhost'
flask_port = 5000

# адрес и порт SNMP-агента
snmp_host = 'localhost'
snmp_port = 5001

# сообщество SNMP
snmp_community = 'public'


@app.route('/snmptrap', methods=['POST'])
def handle_trap():
    """
    Обрабатывает SNMP-трап, полученный от устройства, и сохраняет данные в базе данных.

    :return: JSON-объект со статусом обработки трапа и кодом состояния 201
    """
    data = request.data.decode('utf-8')
    trap_dict = json.loads(data)
    trap_handler.handle_trap(trap_dict)  # используем SNMPTrapHandler для обработки трапа
    return jsonify({'status': 'success'}), 201


def trap_listener():
    """
    Слушает SNMP-трапы, полученные от устройства, и отправляет их на URL-адрес обработчика в Flask.
    """
    while True:
        try:
            for (errorIndication,
                 errorStatus,
                 errorIndex,
                 varBinds) in nextCmd(SnmpEngine(),
                                      CommunityData(snmp_community, mpModel=0),
                                      UdpTransportTarget((snmp_host, snmp_port)),
                                      ContextData(),
                                      ObjectType(ObjectIdentity('SNMPv2-MIB', 'snmpTrapOID'),),
                                      lexicographicMode=False):
                for varBind in varBinds:
                    trap_oid = str(varBind[0])
                    trap_value = str(varBind[1])
                    trap_dict = {"oid": trap_oid, "value": trap_value}
                    trap_json = json.dumps(trap_dict)
                    # отправка SNMP-трапа на URL, обработчик которого предоставлен в Flask
                    url = f'http://{flask_host}:{flask_port}/snmptrap'
                    requests.post(url, data=trap_json)
        except Exception as e:
            logger.error(f"Error while listening for traps: {e}")


if __name__ == '__main__':
    # запуск Flask в отдельном потоке
    import threading
    flask_thread = threading.Thread(target=app.run, kwargs={'host': flask_host, 'port': flask_port})
    flask_thread.start()

    # запуск слушателя SNMP-трапов в главном потоке
    trap_listener()
