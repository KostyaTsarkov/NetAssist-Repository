from flask import Flask, request
import threading
from snmp_trap_receiver import SNMPTrapReceiver
from config import config_data


app = Flask(__name__)

# адрес и порт Flask-приложения
flask_host = config_data["flask_host"]
flask_port = config_data["flask_port"]
num_threads = config_data["num_threads"]


@app.route('/snmptrap', methods=['POST'])
def SNMP_trap():
    """
    Defines a Flask route that receives SNMP traps via an HTTP POST request.
    :return: A string message indicating the successful processing of the SNMP trap.
    """
    trap_dict = request.get_json()
    print(trap_dict)
    # Возвращаем сообщение об успешной обработке SNMP-трапа
    return "SNMP Trap received and processed successfully"


if __name__ == '__main__':
    # Запуск Flask-приложения в отдельном потоке
    flask_thread = threading.Thread(target=app.run, kwargs={'host': flask_host,
                                                            'port': flask_port}
                                    )
    flask_thread.start()

    # Запуск слушателя SNMP-трапов в главном потоке
    receiver = SNMPTrapReceiver(config_data)
    receiver.start(num_threads=num_threads)
    # ...
    receiver.stop()
