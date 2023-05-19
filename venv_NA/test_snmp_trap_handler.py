import pytest
from unittest.mock import MagicMock
from src.snmp_trap_handler import SNMPTrapHandler


@pytest.fixture
def mock_database():
    return MagicMock()

@pytest.fixture
def mock_logger():
    return MagicMock()

def test_snmp_trap_handler_init(mock_database, mock_logger):
    # Проверяем, что объект инициализируется корректно
    community = 'public'
    handler = SNMPTrapHandler(community, mock_database, mock_logger)
    assert handler.community == community
    assert handler.database == mock_database
    assert handler.logger == mock_logger

def test_snmp_trap_handler_handle_trap(mock_database, mock_logger):
    # Проверяем, что метод handle_trap() вызывает правильные методы и логирует сообщение
    trap = {
        'varbind_oid': '1.3.6.1.2.1.2.2.1.7.1',
        'varbind_value': 'up',
        'if_index': 1,
        'if_admin_status': 'up',
        'if_oper_status': 'up',
        'if_in_errors': 0,
        'if_out_errors': 0,
        'if_in_discards': 0,
        'if_out_discards': 0
    }
    handler = SNMPTrapHandler('public', mock_database, mock_logger)
    handler.handle_trap(trap)
    assert mock_database.add_interface.called
    assert mock_logger.log_info.called

def test_snmp_trap_handler_parse_trap():
    # Проверяем, что метод _parse_trap() возвращает правильные значения
    trap = {
        'varbind_oid': '1.3.6.1.2.1.2.2.1.7.1',
        'varbind_value': 'up',
        'if_index': 1,
        'if_admin_status': 'up',
        'if_oper_status': 'up',
        'if_in_errors': 0,
        'if_out_errors': 0,
        'if_in_discards': 0,
        'if_out_discards': 0
    }
    handler = SNMPTrapHandler('public', None, None)
    varbind, interface = handler._parse_trap(trap)
    assert varbind.oid == '1.3.6.1.2.1.2.2.1.7.1'
    assert varbind.value == 'up'
    assert interface.if_index == 1
    assert interface.if_admin_status == 'up'
    assert interface.if_oper_status == 'up'
    assert interface.if_in_errors == 0
    assert interface.if_out_errors == 0
    assert interface.if_in_discards == 0
    assert interface.if_out_discards == 0
