from abc import ABCMeta
from typing import Optional

from pyromhackit.semantics.semantics import Semantics


class Finder(metaclass=ABCMeta):
    def find(self, bs: bytes) -> Optional[Semantics]:
        """
        :return The semantics found by searching through the @bs bytestring, or None if none could be found.
        """
        raise NotImplementedError
