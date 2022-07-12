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

    @staticmethod
    def _freq2score(freq: Dict[bytes, int]) -> float:
        return sum(freq.values())

    def _find_rot(self, bs) -> Optional[Dict[bytes, str]]:
        freqs = self._analyzer.all_word_frequencies(bs)
        scores = {offset: self._freq2score(freq) for offset, freq in freqs.items()}
        if not scores:
            return None
        max_score = max(scores.values())
        if max_score <= 0:
            return None
        max_score_offset = {o for o, s in scores.items() if s == max_score}.pop()
        codec = {bytes([b]): chr((b + max_score_offset) % 256) for b in bs}
        return codec

    def find(self, bs: bytes) -> Optional[Semantics]:
        codec = self._find_rot(bs)
        if codec is None:
            return None
        return Semantics(
            topology=SimpleTopology(1),
            codec=codec,
        )
