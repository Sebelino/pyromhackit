from typing import Dict, Optional

from .analyzer import Analyzer


class RotAnalyzer:

    def __init__(self, analyzer: Analyzer):
        self._analyzer = analyzer

    @classmethod
    def offset_codec(cls, codec: Dict[bytes, str], offset: int):
        d = dict()
        for bs in codec:
            b, = bs
            d[bytes([(b - offset) % 256])] = chr(b)
        return d

    def all_word_frequencies(self, bs: bytes) -> Dict[int, Dict[bytes, int]]:
        freqs = dict()
        for offset in range(256):
            rotated_bs = bytes([(b + offset) % 256 for b in bs])
            freq = self._analyzer.word_frequency(rotated_bs)
            if not freq:
                continue
            freqs[offset] = freq
        return freqs

    def find_rot(self, bs) -> Optional[Dict[bytes, str]]:
        freqs = self.all_word_frequencies(bs)
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
