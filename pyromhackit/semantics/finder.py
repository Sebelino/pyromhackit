from abc import ABCMeta

from pyromhackit.semantics.semantics import Semantics


class Finder(metaclass=ABCMeta):
    def find(self, bs: bytes) -> Semantics:
        """ :return Any semantics meaningful for the @bs bytestring. """
        raise NotImplementedError
