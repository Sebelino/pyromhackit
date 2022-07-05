from .semantics import Semantics
from pyromhackit.topology.simple_topology import SimpleTopology


class SimpleMonobyteFinder:
    @staticmethod
    def find(bs: bytes) -> Semantics:
        codec = {
            b"H": "H",
            b"e": "e",
            b"l": "l",
            b"o": "o",
            b"&": "&",
            b"$": "$",
        }
        topology = SimpleTopology(1)
        return Semantics(topology=topology, codec=codec)
