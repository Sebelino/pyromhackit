import ast
import json
from typing import Dict, Optional

from .analyzer import Analyzer


def persist_to_file():
    def decorator(original_func):
        def new_func(self, bs: bytes):
            try:
                with open(self.path, 'r') as f:
                    cache = json.load(f)
            except (IOError, ValueError):
                cache = dict()
            bs_repr = repr(bs)
            if bs_repr not in cache:
                dct = original_func(self, bs)
                cache[bs_repr] = {offset: {repr(w): c for w, c in d.items()} for offset, d in dct.items()}
                with open(self.path, "w") as f:
                    json.dump(cache, f)  # Note, offset is stored as a string in JSON
                return dct
            return {int(offset): {ast.literal_eval(bs): wc for bs, wc in wordcount.items()} for offset, wordcount in
                    cache[bs_repr].items()}

        return new_func

    return decorator


class RotAnalyzer:

    def __init__(self, analyzer: Analyzer):
        self._analyzer = analyzer
        self.path = "/tmp/rothoy.json"

    @classmethod
    def offset_codec(cls, codec: Dict[bytes, str], offset: int):
        d = dict()
        for bs in codec:
            b, = bs
            d[bytes([(b - offset) % 256])] = chr(b)
        return d

    @persist_to_file()
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