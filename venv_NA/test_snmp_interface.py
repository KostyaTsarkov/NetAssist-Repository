from src.snmp_interface import SNMPInterface


def test_snmp_interface_init():
    admin_status = 1
    oper_status = 2
    in_errors = 3
    out_errors = 4
    in_discards = 5
    out_discards = 6
    interface = SNMPInterface(admin_status, oper_status, in_errors, out_errors, in_discards, out_discards)
    assert interface.if_admin_status == admin_status
    assert interface.if_oper_status == oper_status
    assert interface.if_in_errors == in_errors
    assert interface.if_out_errors == out_errors
    assert interface.if_in_discards == in_discards
    assert interface.if_out_discards == out_discards


def test_snmp_interface_to_dict():
    admin_status = 1
    oper_status = 2
    in_errors = 3
    out_errors = 4
    in_discards = 5
    out_discards = 6
    interface = SNMPInterface(admin_status, oper_status, in_errors, out_errors, in_discards, out_discards)
    expected_dict = {
        'if_admin_status': admin_status,
        'if_oper_status': oper_status,
        'if_in_errors': in_errors,
        'if_out_errors': out_errors,
        'if_in_discards': in_discards,
        'if_out_discards': out_discards
    }
    assert interface.to_dict() == expected_dict
