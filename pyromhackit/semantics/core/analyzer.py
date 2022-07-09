import ast
import json
from typing import Dict, Optional


def persist_to_file(original_func):
    def new_func(self: 'Analyzer', bs: bytes):
        try:
            with open(self.path, 'r') as f:
                cache = json.load(f)
        except (IOError, ValueError):
            cache = dict()

        bs_repr = repr(bs)
        if bs_repr not in cache:
            dct = original_func(self, bs)
            cache[bs_repr] = {repr(word): wordcount for word, wordcount in dct.items()}
            with open(self.path, "w") as f:
                json.dump(cache, f)
            return dct
        return {ast.literal_eval(string_bs): value for string_bs, value in cache[bs_repr].items()}

    return new_func


class Analyzer:

    def __init__(self, dictionary):
        self._dictionary = dictionary
        self.path = "/tmp/pyromhackit_word_frequency.json"

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

    def find(self, bs: bytes) -> Optional[Dict[bytes, str]]:
        codec = {bytes([b]): chr(b) for b in bs}
        freq = self.word_frequency(bs)
        if len(freq) == 0:
            return None
        return codec
