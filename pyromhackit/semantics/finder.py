from .english_dictionary import EnglishDictionary
from .exception import SemanticsNotFoundException
from .semantics import Semantics
from pyromhackit.topology.simple_topology import SimpleTopology


class SimpleMonobyteFinder:
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

    @classmethod
    def find(cls, bs: bytes) -> Semantics:
        codec = {bytes([b]): bytes([b]).decode() for b in bs}
        topology = SimpleTopology(1)
        dictionary = EnglishDictionary()
        matches = dict()
        for word in dictionary.iterbytestrings():
            matches[word] = cls.count_matches(word, bs.lower())
        matches = {w: c for w, c in matches.items() if c >= 1}
        if len(matches) == 0:
            raise SemanticsNotFoundException()
        return Semantics(topology=topology, codec=codec)
