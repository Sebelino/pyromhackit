from typing import Optional, Dict

from pyromhackit.topology.simple_topology import SimpleTopology
from ..core.analyzer import Analyzer
from ..english_dictionary import EnglishDictionary
from ..finder import Finder
from ..semantics import Semantics


class SimpleMonobyteFinder(Finder):
    def __init__(self):
        self._analyzer = Analyzer(EnglishDictionary())

    def _find_codec(self, bs: bytes) -> Optional[Dict[bytes, str]]:
        codec = {bytes([b]): chr(b) for b in bs}
        freq = self._analyzer.word_frequency(bs)
        if len(freq) == 0:
            return None
        return codec

    def find(self, bs: bytes) -> Optional[Semantics]:
        codec = self._find_codec(bs)
        if codec is None:
            return None
        return Semantics(topology=SimpleTopology(1), codec=codec)
