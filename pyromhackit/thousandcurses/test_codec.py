#!/usr/bin/env python

"""
Tests for checking the bijective property of codecs.
"""

import pytest
import os

from .codec import Codec, codecnames, decodernames, UppercaseASCII, Tree

package_dir = os.path.dirname(os.path.abspath(__file__))


def bytestrings(n):
    """ Returns a generator for bytestrings of length n. """
    for i in range(n):
        lst = [i >> i * j for j in range(n)]
        yield bytes(lst)


class TestBijection:
    def setup_class(self):
        self.bytestrings = [bytes([i]) for i in range(2 ** 8)]
        self.strings = [chr(i) for i in range(2 ** 8)]

    @pytest.mark.parametrize("decodername", decodernames.keys())
    def test_totality(self, decodername):
        """ Every bytestring can decoded """
        cdc = decodernames[decodername]
        returned = ""
        for bs in self.bytestrings:
            returned = cdc.decode(bs)
            if not isinstance(returned, str):
                break
        assert isinstance(returned, str)

    @pytest.mark.parametrize("decodername", decodernames.keys())
    def test_injective_decoding(self, decodername):
        """ x != y -> decode(x) != decode(y) for all bytestrings x, y """
        cdc = decodernames[decodername]
        inverse_graph = dict()
        for bs in self.bytestrings:
            d = cdc.decode(bs)
            if d in inverse_graph:
                raise AssertionError(
                    "Injective property for {0} failed beause decode({1}) = decode({2}) = {3}".format(decodername, bs,
                                                                                                      inverse_graph[
                                                                                                          d], d))
            inverse_graph[d] = bs

    @pytest.mark.parametrize("codecname", codecnames.keys())
    def test_left_invertibility(self, codecname):
        """ x == encode(decode(x)) for all bytestrings x """
        cdc = codecnames[codecname]
        for bs in self.bytestrings:
            d = cdc.decode(bs)
            e = cdc.encode(d)
            if e != bs:
                break
        assert e == bs

    @pytest.mark.skip(reason="TODO")
    def test_right_invertibility(self):
        """ x == decode(encode(x)) for all strings x """


def test_instantiate_abstract():
    with pytest.raises(NotImplementedError):
        Codec.decode(b"")
    with pytest.raises(NotImplementedError):
        Codec.encode("")


@pytest.mark.parametrize("bytestr, expected", [
    (b'', ([b''], [""], dict())),
    (b'Abc', ([b'A', b'b', b'c'], ["A", "B", "C"], {(0,): {(0,)}, (1,): {(1,)}, (2,): {(2,)}})),
    (b'AbCD', ([b'A', b'b', b'C', b'D'], ["A", "B", "C", "D"], {(0,): {(0,)}, (1,): {(1,)}, (2,): {(2,)}, (3,): {(3,)}})),
])
def test_mapping_UppercaseASCII(bytestr, expected):
    b, s, f = UppercaseASCII.mapping(bytestr)
    assert_mapping(bytestr, UppercaseASCII, (Tree(b), Tree(s), f))
    assert (b, s, f) == expected


def assert_mapping(bytestr, decoder, mapping):
    b, s, f = mapping
    assert any(isinstance(b, tpe) for tpe in {bytes, Tree})
    assert b.flatten() == bytestr
    assert any(isinstance(s, tpe) for tpe in {str, Tree})
    assert s.flatten() == decoder.decode(bytestr)
    assert isinstance(f, dict)
    assert all(isinstance(bl, tuple) for bl in f)
    assert all(isinstance(i, int) for bl in f for i in bl)
    assert all(isinstance(v, set) for v in f.values())
    assert all(isinstance(sl, tuple) for v in f.values() for sl in v)
    assert all(isinstance(i, int) for v in f.values() for sl in v for i in sl)
    for bl, sls in f.items():
        complement = {x for y in f.values() for x in y}
        for bl2 in bytestrings(len(bl)):
            sl2 = decoder.decode(bl2)
            assert sl2 not in complement


class TestTree(object):
    @pytest.mark.parametrize("arg, expected", [
        ([], ValueError),
        ([b''], 1),
        ([b'',b'a'], 2),
        ([b'',[b'a']], 2),
        ([b'',[b'a', b'bc']], 2),
    ])
    def test_len(self, arg, expected):
        if expected is ValueError:
            with pytest.raises(ValueError):
                Tree(arg)
        else:
            assert len(Tree(arg)) == expected

    @pytest.mark.parametrize("arg, expected", [
        ([b''], b''),
        ([b'abc'], b'abc'),
        ([b'abc', b'def'], b'abcdef'),
        ([b'abc', [b'd'], b'ef'], b'abcdef'),
        ([b'ab', [b'c', b'd'], b'ef'], b'abcdef'),
        ([''], ''),
        (['a', ['b', 'c', [['d']]], 'ef'], 'abcdef'),
    ])
    def test_flatten(self, arg, expected):
        assert Tree(arg).flatten() == expected

    @pytest.mark.parametrize("expected", [
        [b''],
        [b'a', b'b'],
        [b'a', [[b'c']], b'b'],
    ])
    def test_list(self, expected):
        returned = Tree(expected).list()
        assert returned == expected
