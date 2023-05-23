from snmp_trap import SNMPTrap

trap_dict = dict()
var_bind_list = [{'oid': '1.3.6.1.2.1.1.5.0', 'value': '1'},{'oid': '1.3.6.1.2.1.1.6.0', 'value': '2'}]
trap_dict = {
                'enterprise': '',
                'agent_address': '',
                'generic_trap': '',
                'specific_trap': '',
                'time_stamp': '',
                'var_binds': var_bind_list
}
print(trap_dict)
result = trap_dict.get('var_binds')
for oid in result:
    print(oid.get('oid'))
#print(result[1])