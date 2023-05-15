from flask import Flask, request, jsonify
from src.snmp_trap_handler import SNMPTrapHandler
from src.database import Database
from src.logger import Logger

app = Flask(__name__)

database = Database('interfaces.db')
logger = Logger('app.log')
trap_handler = SNMPTrapHandler('public', database, logger)


@app.route('/snmp-trap', methods=['POST'])
def handle_snmp_trap():
    data = request.get_json()
    # Обработка трапа
    interface = {
        'if_index': data['if_index'],
        'if_admin_status': data['if_admin_status'],
        'if_oper_status': data['if_oper_status'],
        'if_in_errors': data['if_in_errors'],
        'if_out_errors': data['if_out_errors'],
        'if_in_discards': data['if_in_discards'],
        'if_out_discards': data['if_out_discards']
    }
    database.add_interface(interface)  # Сохранение информации об интерфейсе в базе данных
    return jsonify({'status': 'success'}), 201


if __name__ == '__main__':
    app.run(debug=True)
