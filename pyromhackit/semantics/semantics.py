from dataclasses import dataclass
from typing import Dict

from pyromhackit.topology.topology import Topology


@dataclass(frozen=True)
class Semantics:
    topology: Topology
    codec: Dict[bytes, str]
