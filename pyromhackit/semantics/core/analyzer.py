import ast
import json
from typing import Dict


def persist_to_file(original_func):
    def unpack_bytestring_key(dct: dict) -> dict:
        return {ast.literal_eval(bs_repr): v for bs_repr, v in dct.items()}

    def unpack_cache(cache: Dict[str, Dict[str, int]]) -> Dict[bytes, Dict[bytes, int]]:
        return unpack_bytestring_key({k: unpack_bytestring_key(v) for k, v in cache.items()})

    def load_cache(path: str) -> Dict[str, Dict[str, int]]:
        try:
            with open(path, 'r') as f:
                cache = json.load(f)
        except (IOError, ValueError):
            cache = dict()
        return cache

    def pack_cache(dct: dict) -> dict:
        return {repr(bs): {repr(bs2): c for bs2, c in counts.items()} for bs, counts in dct.items()}

    def save_cache(path: str, dct: dict):
        with open(path, "w") as f:
            json.dump(dct, f)

    def new_func(self: 'Analyzer', bs: bytes):
        if self._inmemory_cache is None:
            self._inmemory_cache = unpack_cache(load_cache(self.path))
        if bs in self._inmemory_cache:
            return self._inmemory_cache[bs]
        dct = original_func(self, bs)
        self._inmemory_cache[bs] = dct
        save_cache(self.path, pack_cache(self._inmemory_cache))
        return dct

    return new_func


class Analyzer:

    def __init__(self, dictionary):
        self._dictionary = dictionary
        self.path = "/tmp/pyromhackit_word_frequency.json"
        self._inmemory_cache = None

    @staticmethod
    def count_matches(word: bytes, bytestring: bytes) -> int:
        index = 0
        count = 0
        while index < len(bytestring):
            index = bytestring.find(word, index)
            if index == -1:
                break
            count += 1
            index += len(word)
        return count

    @persist_to_file
    def word_frequency(self, bs: bytes) -> Dict[bytes, int]:
        matches = dict()
        bs_lowercased = bs.lower()
        for word in self._dictionary.iterbytestrings():
            count = self.count_matches(word, bs_lowercased)
            if count == 0:
                continue
            matches[word] = count
        return matches
