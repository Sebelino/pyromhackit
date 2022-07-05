from ..exception import SemanticsNotFoundException
from ..finder import Finder
from ..semantics import Semantics


class RotatingMonobyteFinder(Finder):
    def __init__(self, finder: Finder):
        self._finder = finder

    def find(self, bs: bytes) -> Semantics:
        matches = dict()
        for offset in range(256):
            offset_bs = bytes([(b + offset) % 256 for b in bs])
            try:
                semantics = self._finder.find(offset_bs)
                matches[offset] = semantics
            except SemanticsNotFoundException:
                continue
        if len(matches) != 1:
            raise SemanticsNotFoundException
        return next(iter(matches.values()))
