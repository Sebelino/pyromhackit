from .finder import SimpleMonobyteFinder
from .semantics import Semantics


def test_finder():
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
