import pytest

from .finder import RotatingMonobyteFinder
from ..finder import Finder
from ..search_result import SearchResult
from ..semantics import Semantics
from ...topology.simple_topology import SimpleTopology


class LeetFinder(Finder):
    def find(self, bs: bytes) -> SearchResult:
        if b"1337" not in bs.lower():
            return SearchResult(tuple())
        codec = {bytes([b]): chr(b) for b in bs}
        semantics = Semantics(
            topology=SimpleTopology(1),
            codec=codec,
        )
        return SearchResult((semantics,))


@pytest.fixture
def finder():
    return RotatingMonobyteFinder(LeetFinder())


def test_finder_rot0(finder):
    result = finder.find(b"hoy1337doy")
    assert len(result.semantics_set) == 1


def test_finder_rot1(finder):
    result = finder.find(b"ipz2448epz")
    assert len(result.semantics_set) == 1


def test_finder_rot255(finder):
    result = finder.find(b"gnx0226cnx")
    assert len(result.semantics_set) == 1


def test_finder_no_match(finder):
    result = finder.find(b"hoy1338doy")
    assert len(result.semantics_set) == 0


def test_finder_multiple_matches(finder):
    result = finder.find(b"1337 and 2448")
    assert len(result.semantics_set) == 2


def test_finder_multiple_matches_check_codecs(finder):
    bytestring = b"1337hoy2448"
    result = finder.find(bytestring)

    s1 = result.semantics_set[0]
    tree1 = s1.topology.structure(bytestring)
    string1 = "".join([s1.codec[bs] for bs in tree1])

    s2 = result.semantics_set[1]
    tree2 = s2.topology.structure(bytestring)
    string2 = "".join([s2.codec[bs] for bs in tree2])

    assert {string1, string2} == {
        "1337hoy2448",
        "0226gnx1337",
    }
