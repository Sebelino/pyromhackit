from .semantics import Semantics
from pyromhackit.topology.simple_topology import SimpleTopology


class SimpleMonobyteFinder:
    @staticmethod
    def find(bs: bytes) -> Semantics:
        codec = {bytes([b]): bytes([b]).decode() for b in bs}
        topology = SimpleTopology(1)
        return Semantics(topology=topology, codec=codec)
