import threading

from flask import Flask, request

from config import config_data
from nb_ipam_api import manage_ip
from snmp_trap_receiver import SNMPTrapReceiver
from nb_mng_int_cable import mng_cable, mng_int


# Create a Flask instance
app = Flask(__name__)

# адрес и порт Flask-приложения
flask_host = config_data["flask_host"]
flask_port = config_data["flask_port"]
num_threads = config_data["num_threads"]


@app.route('/snmptrap',
           methods=['POST'])
def SNMP_trap():
    trap_dict = request.get_json()
    print(trap_dict)
    return "SNMP Trap received and processed successfully"


app.add_url_rule("/api/fixed_ip",
                 methods=["POST"],
                 view_func=manage_ip)

app.add_url_rule("/api/cable_change",
                 methods=['POST'],
                 view_func=mng_cable)

app.add_url_rule("/api/int_update",
                 methods=['POST'],
                 view_func=mng_int)

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
