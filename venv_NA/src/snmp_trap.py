from dataclasses import dataclass
from typing import List
from snmp_var_bind import SNMPVarBind


@dataclass
class SNMPTrap:
    """
    Represents an SNMP trap message.
    """
    enterprise: str
    agent_address: str
    generic_trap: str
    specific_trap: str
    time_stamp: float
    var_binds: List[SNMPVarBind]
