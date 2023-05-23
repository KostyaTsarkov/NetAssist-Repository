from dataclasses import dataclass
from typing import List
from snmp_var_bind import SNMPVarBind


@dataclass
class SNMPTrap:
    enterprise: str
    agent_address: str
    generic_trap: str
    specific_trap: str
    time_stamp: str
    var_binds: List[SNMPVarBind]
