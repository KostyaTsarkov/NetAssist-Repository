import json
import pytest
from src.app import app, database

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_handle_snmp_trap(client):
    data = {
        'varbind_oid': '1.3.6.1.2.1.2.2.1.7.1',
        'varbind_value': 2,
        'if_index': 1,
        'if_admin_status': 1,
        'if_oper_status': 2,
        'if_in_errors': 0,
        'if_out_errors': 0,
        'if_in_discards': 0,
        'if_out_discards': 0
    }
    response = client.post('/snmp-trap', data=json.dumps(data), content_type='application/json')
    assert response.status_code == 201
    assert response.json == {'status': 'success'}
    interfaces = database.get_interfaces()
    assert len(interfaces) == 1
    interface = interfaces[0]
    assert interface['if_index'] == 1
    assert interface['if_admin_status'] == 1
    assert interface['if_oper_status'] == 2
    assert interface['if_in_errors'] == 0
    assert interface['if_out_errors'] == 0
    assert interface['if_in_discards'] == 0
    assert interface['if_out_discards'] == 0
    database.add_interface(interface)
