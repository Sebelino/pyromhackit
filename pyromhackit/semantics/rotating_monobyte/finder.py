from ..finder import Finder
from ..search_result import SearchResult


class RotatingMonobyteFinder(Finder):
    def __init__(self, finder: Finder):
        self._finder = finder

    def find(self, bs: bytes) -> SearchResult:
        matches = dict()
        for offset in range(256):
            offset_bs = bytes([(b + offset) % 256 for b in bs])
            result = self._finder.find(offset_bs)
            if len(result.semantics_set) == 0:
                continue
            if len(result.semantics_set) >= 2:
                raise NotImplementedError
            semantics, = result.semantics_set
            matches[offset] = semantics
        return SearchResult(tuple(s for s in matches.values()))
