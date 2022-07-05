import pytest

from .finder import SimpleMonobyteFinder, SemanticsNotFoundException
from .semantics import Semantics


def test_finder_hello():
    finder = SimpleMonobyteFinder()
    bytestring = b"&&Hello$$$"
    returned = finder.find(bytestring)
    assert isinstance(returned, Semantics)
    assert returned.codec.keys() == {b"&", b"$", b"H", b"e", b"l", b"o"}
    assert {
        (b"H", "H"),
        (b"e", "e"),
        (b"l", "l"),
        (b"o", "o"),
    }.issubset(returned.codec.items())
    byteslist = returned.topology.structure(bytestring)
    assert b"".join(byteslist) == bytestring
    stringlist = [returned.codec[bs] for bs in byteslist]
    assert stringlist == ["&", "&", "H", "e", "l", "l", "o", "$", "$", "$"]


def test_finder_world():
    finder = SimpleMonobyteFinder()
    bytestring = b"&&World"
    returned = finder.find(bytestring)
    assert isinstance(returned, Semantics)
    assert returned.codec.keys() == {b"&", b"W", b"o", b"r", b"l", b"d"}
    assert {
        (b"W", "W"),
        (b"o", "o"),
        (b"r", "r"),
        (b"l", "l"),
        (b"d", "d"),
    }.issubset(returned.codec.items())
    byteslist = returned.topology.structure(bytestring)
    assert b"".join(byteslist) == bytestring
    stringlist = [returned.codec[bs] for bs in byteslist]
    assert stringlist == ["&", "&", "W", "o", "r", "l", "d"]


def test_finder_finds_nothing():
    finder = SimpleMonobyteFinder()
    bytestring = b".%$~,&"
    with pytest.raises(SemanticsNotFoundException):
        finder.find(bytestring)
