from ..english_dictionary import EnglishDictionary
from ..finder import Finder
from ..search_result import SearchResult
from pyromhackit.topology.simple_topology import SimpleTopology
from ..semantics import Semantics


class SimpleMonobyteFinder(Finder):
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

    def find(self, bs: bytes) -> SearchResult:
        codec = {bytes([b]): chr(b) for b in bs}
        topology = SimpleTopology(1)
        dictionary = EnglishDictionary()
        matches = dict()
        for word in dictionary.iterbytestrings():
            matches[word] = self.count_matches(word, bs.lower())
        matches = {w: c for w, c in matches.items() if c >= 1}
        if len(matches) == 0:
            return SearchResult(tuple())
        semantics = Semantics(topology=topology, codec=codec)
        return SearchResult((semantics,))
