from src.snmp_var_bind import SNMPVarBind


def test_snmp_varbind_init():
    oid = '1.3.6.1.2.1.2.2.1.7.1'
    value = 'up'
    varbind = SNMPVarBind(oid, value)
    assert varbind.oid == oid
    assert varbind.value == value


def test_snmp_varbind_to_dict():
    oid = '1.3.6.1.2.1.2.2.1.7.1'
    value = 'up'
    varbind = SNMPVarBind(oid, value)
    expected_dict = {'oid': oid, 'value': value}
    assert varbind.to_dict() == expected_dict
