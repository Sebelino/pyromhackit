from ..exception import SemanticsNotFoundException
from ..finder import Finder
from ..search_result import SearchResult


class RotatingMonobyteFinder(Finder):
    def __init__(self, finder: Finder):
        self._finder = finder

    def find(self, bs: bytes) -> SearchResult:
        matches = dict()
        for offset in range(256):
            offset_bs = bytes([(b + offset) % 256 for b in bs])
            try:
                result = self._finder.find(offset_bs)
                semantics, = result.semantics_set
                matches[offset] = semantics
            except SemanticsNotFoundException:
                continue
        if len(matches) != 1:
            raise SemanticsNotFoundException
        semantics = next(iter(matches.values()))
        return SearchResult((semantics,))
