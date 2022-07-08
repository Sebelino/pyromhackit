from typing import Dict, Optional

from pyromhackit.semantics.core.persist_to_file import persist_to_file


class Analyzer:

    def __init__(self, dictionary):
        self._dictionary = dictionary

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

    @staticmethod
    @persist_to_file(path="/tmp/word_frequency.json")
    def word_frequency_static(bs: bytes, dictionary, count_matches_func):
        matches = dict()
        bs_lowercased = bs.lower()
        for word in dictionary.iterbytestrings():
            count = count_matches_func(word, bs_lowercased)
            if count == 0:
                continue
            matches[word] = count
        return matches

    def word_frequency(self, bs: bytes) -> Dict[bytes, int]:
        return self.word_frequency_static(bs, self._dictionary, self.count_matches)

    def find(self, bs: bytes) -> Optional[Dict[bytes, str]]:
        codec = {bytes([b]): chr(b) for b in bs}
        freq = self.word_frequency(bs)
        if len(freq) == 0:
            return None
        return codec
