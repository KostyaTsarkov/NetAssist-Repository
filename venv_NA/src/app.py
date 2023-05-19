from flask import Flask, request, jsonify
import requests
import json
from pysnmp.carrier.asyncore.dispatch import AsyncoreDispatcher
from pysnmp.carrier.asyncore.dgram import udp
from snmp_trap_handler import SNMPTrapHandler
from database import Database
from logger import Logger
from config import config_data


app = Flask(__name__)

# создание объектов для работы с базой данных и логирования
database = Database(config_data["database"])
logger = Logger(config_data["logger"])

# адрес и порт Flask-приложения
flask_host = config_data["flask_host"]
flask_port = config_data["flask_port"]

# адрес и порт SNMP-агента
snmp_host = config_data["snmp_host"]
snmp_port = config_data["snmp_port"]

# сообщество SNMP
snmp_community = config_data["community"]

# создаем объект SNMPTrapHandler
trap_handler = SNMPTrapHandler(snmp_community, database, logger)



@app.route('/snmptrap', methods=['POST'])
def handle_trap():
    """
    Обрабатывает SNMP-трап, полученный от устройства,
    и сохраняет данные в базе данных.

    :return: JSON-объект со статусом обработки трапа и кодом состояния 201
    """
    data = request.data.decode('utf-8')
    trap_dict = json.loads(data)
    # используем SNMPTrapHandler для обработки трапа
    trap_handler.handle_SNMP_trap(trap_dict)
    return jsonify({'status': 'success'}), 201


def listener_SNMP_trap():
    """
    Слушает SNMP-трапы, полученные от устройства,
    и отправляет их на URL-адрес обработчика в Flask.
    """
    # создаем диспетчер
    dispatcher = AsyncoreDispatcher()

    # создаем UDP-транспорт
    transport = udp.UdpSocketTransport().openServerMode((snmp_host, snmp_port))

    # регистрируем обработчик
    """ def handle_trap(_, __, ___, ____, pdu):
        # извлекаем данные из PDU
        trap_oid = str(pdu[3][0][0])
        trap_value = str(pdu[3][0][1])
        trap_dict = {"oid": trap_oid, "value": trap_value}
        trap_json = json.dumps(trap_dict)
        # отправляем данные на URL-адрес обработчика в Flask
        url = f'http://{flask_host}:{flask_port}/snmptrap'
        requests.post(url, data=trap_json) """

    def message_handler(msg):
        print("Received message:", msg)
    
    dispatcher.registerRecvCbFun(message_handler)

    # запускаем диспетчер
    dispatcher.registerTransport(udp.domainName, transport)
    dispatcher.jobStarted(1)
    dispatcher.runDispatcher()

    """try:
        # начинаем бесконечный цикл обработки событий
        dispatcher.runDispatcher()
    except:
        dispatcher.closeDispatcher() """


if __name__ == '__main__':
    # запуск Flask в отдельном потоке
    import threading
    flask_thread = threading.Thread(target=app.run, kwargs={'host': flask_host,
                                                            'port': flask_port}
                                    )
    flask_thread.start()

    # запуск слушателя SNMP-трапов в главном потоке
    listener_SNMP_trap()
