import pytest

from .finder import RotatingMonobyteFinder
from ..exception import SemanticsNotFoundException
from ..finder import Finder
from ..semantics import Semantics
from ...topology.simple_topology import SimpleTopology


class LeetFinder(Finder):
    def find(self, bs: bytes) -> Semantics:
        if b"1337" not in bs.lower():
            raise SemanticsNotFoundException
        codec = {bytes([b]): bytes([b]).decode() for b in bs}
        return Semantics(
            topology=SimpleTopology(1),
            codec=codec,
        )


@pytest.fixture
def finder():
    return RotatingMonobyteFinder(LeetFinder())


def test_finder_rot0(finder):
    finder.find(b"hoy1337doy")


def test_finder_rot1(finder):
    finder.find(b"ipz2448epz")


def test_finder_rot255(finder):
    finder.find(b"gnx0226cnx")


def test_finder_no_match(finder):
    with pytest.raises(SemanticsNotFoundException):
        finder.find(b"hoy1338doy")
