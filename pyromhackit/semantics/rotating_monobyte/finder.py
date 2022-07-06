from typing import Optional

from ..core.analyzer import Analyzer
from ..core.rot_analyzer import RotAnalyzer
from ..english_dictionary import EnglishDictionary
from ..finder import Finder
from ..semantics import Semantics
from ...topology.simple_topology import SimpleTopology


class RotatingMonobyteFinder(Finder):
    def __init__(self, dictionary=EnglishDictionary()):
        self._analyzer = RotAnalyzer(Analyzer(dictionary))

    def find(self, bs: bytes) -> Optional[Semantics]:
        codec = self._analyzer.find_rot(bs)
        if codec is None:
            return None
        return Semantics(
            topology=SimpleTopology(1),
            codec=codec,
        )
