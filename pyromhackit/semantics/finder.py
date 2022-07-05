from abc import ABCMeta

from pyromhackit.semantics.search_result import SearchResult


class Finder(metaclass=ABCMeta):
    def find(self, bs: bytes) -> SearchResult:
        """ :return The result of searching through the @bs bytestring. """
        raise NotImplementedError
