from typing import Dict

from ..finder import Finder
from ..search_result import SearchResult
from ..semantics import Semantics


class RotatingMonobyteFinder(Finder):
    def __init__(self, finder: Finder):
        self._finder = finder

    @classmethod
    def offset_codec(cls, codec: Dict[bytes, str], offset: int):
        d = dict()
        for bs in codec:
            b, = bs
            d[bytes([(b - offset) % 256])] = chr(b)
        return d

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
            codec = self.offset_codec(semantics.codec, offset)
            semantics = Semantics(
                topology=semantics.topology,
                codec=codec,
            )
            matches[offset] = semantics
        return SearchResult(tuple(s for s in matches.values()))
