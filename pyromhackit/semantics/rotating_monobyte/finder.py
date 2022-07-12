from typing import Optional, Dict, Tuple

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
    def _freq2score_tuple(freq: Dict[bytes, int]) -> Tuple[float]:
        """ @return: A tuple (i1, i2, i3, ...) where in is the number of found words of length n. """
        max_word_length = max(len(word) for word in freq.keys())
        score_list = [0.0] * max_word_length
        scores = dict()
        for word, wordcount in freq.items():
            if len(word) not in scores:
                scores[len(word)] = 0
            scores[len(word)] += wordcount
        for word_length, count in scores.items():
            score_list[word_length - 1] = count
        return tuple(score_list)

    @staticmethod
    def _normalize_score_tuples(score_dict: Dict[int, Tuple[float]]) -> Dict[int, Tuple[float]]:
        if not score_dict:
            return score_dict
        max_tuple_length = max(len(tpl) for tpl in score_dict.values())
        for cutoff_index in range(max_tuple_length):
            vertical_scores = {tpl[cutoff_index] if cutoff_index < len(tpl) else 0.0 for tpl in score_dict.values()}
            if vertical_scores == {0.0}:
                continue
            return {offset: tpl[cutoff_index:] for offset, tpl in score_dict.items()}
        return score_dict

    @staticmethod
    def _scoretuple2score(score_tuple: Tuple[float]) -> float:
        return sum(s * 10 ** i for i, s in enumerate(score_tuple))

    def _find_rot(self, bs) -> Optional[Dict[bytes, str]]:
        freqs = self._analyzer.all_word_frequencies(bs)
        tscores = {offset: self._freq2score_tuple(freq) for offset, freq in freqs.items()}
        tscores = self._normalize_score_tuples(tscores)
        scores = {offset: self._scoretuple2score(score_tuple) for offset, score_tuple in tscores.items()}
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
