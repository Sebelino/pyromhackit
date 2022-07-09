import json
from typing import Dict, Optional

from .analyzer import Analyzer


def persist_to_file(path: str):
    def decorator(original_func):
        try:
            with open(path, 'r') as f:
                cache = json.load(f)
        except (IOError, ValueError) as e:
            cache = dict()

        def new_func(cache_param: bytes, *args):
            cache_param_str = repr(cache_param)
            if cache_param_str not in cache:
                dct = original_func(cache_param, *args)
                cache[cache_param_str] = {offset: {repr(w): c for w, c in d.items()} for offset, d in dct.items()}
                with open(path, "w") as f:
                    json.dump(cache, f)
            return cache[cache_param_str]

        return new_func

    return decorator


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

    @staticmethod
    @persist_to_file(path="/tmp/all_word_frequencies.json")
    def all_word_frequencies_static(bs: bytes, analyzer: Analyzer) -> Dict[int, Dict[bytes, int]]:
        freqs = dict()
        for offset in range(256):
            rotated_bs = bytes([(b + offset) % 256 for b in bs])
            freq = analyzer.word_frequency(rotated_bs)
            if not freq:
                continue
            freqs[offset] = freq
        return freqs

    def all_word_frequencies(self, bs: bytes) -> Dict[int, Dict[bytes, int]]:
        return self.all_word_frequencies_static(bs, self._analyzer)

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
