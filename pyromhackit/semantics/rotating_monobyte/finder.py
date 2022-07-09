from typing import Optional, Dict

from ..core.analyzer import Analyzer
from ..core.rot_analyzer import RotAnalyzer
from ..english_dictionary import EnglishDictionary
from ..finder import Finder
from ..semantics import Semantics
from ...topology.simple_topology import SimpleTopology


class RotatingMonobyteFinder(Finder):
    def __init__(self, dictionary=EnglishDictionary()):
        self._analyzer = RotAnalyzer(Analyzer(dictionary))

    def _find_rot(self, bs) -> Optional[Dict[bytes, str]]:
        freqs = self._analyzer.all_word_frequencies(bs)
        max_offset = None
        max_score = 0
        for offset, freq in freqs.items():
            score = sum(freq.values())
            if score > max_score:
                max_score = score
                max_offset = offset
        if max_offset is None:
            return None
        codec = {bytes([b]): chr((b + max_offset) % 256) for b in bs}
        return codec

    def find(self, bs: bytes) -> Optional[Semantics]:
        codec = self._find_rot(bs)
        if codec is None:
            return None
        return Semantics(
            topology=SimpleTopology(1),
            codec=codec,
        )
