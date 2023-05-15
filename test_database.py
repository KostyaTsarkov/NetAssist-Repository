from unittest.mock import MagicMock
import pytest

from src.snmp_interface import SNMPInterface
from src.database import Database

def test_database_init():
    db_name = 'test_db'
    db = Database(db_name)
    assert db.db_name == db_name
    assert not db.connected

def test_database_connect():
    db = Database('test_db')
    assert not db.connected
    assert db.connect()
    assert db.connected

def test_database_disconnect():
    db = Database('test_db')
    assert not db.connected
    assert not db.disconnect()
    db.connect()
    assert db.connected
    assert db.disconnect()
    assert not db.connected

def test_database_save_interface():
    db = Database('test_db')
    interface = SNMPInterface(1, 2, 3, 4, 5, 6)
    assert not db.save_interface(interface)
    db.connect()
    assert db.save_interface(interface)

def test_database_get_interfaces():
    db = Database('test_db')
    assert not db.get_interfaces()
    db.connect()
    assert isinstance(db.get_interfaces(), list)

