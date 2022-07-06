from typing import Optional

from pyromhackit.topology.simple_topology import SimpleTopology
from ..core.analyzer import Analyzer
from ..english_dictionary import EnglishDictionary
from ..finder import Finder
from ..semantics import Semantics


class SimpleMonobyteFinder(Finder):
    def __init__(self):
        self._analyzer = Analyzer(EnglishDictionary())

    def find(self, bs: bytes) -> Optional[Semantics]:
        codec = self._analyzer.find(bs)
        if codec is None:
            return None
        return Semantics(topology=SimpleTopology(1), codec=codec)
