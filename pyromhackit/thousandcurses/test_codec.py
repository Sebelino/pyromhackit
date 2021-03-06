#!/usr/bin/env python

"""
Tests for checking the bijective property of codecs.
"""

import pytest
import os

from pyromhackit.thousandcurses.codec import Codec, ourcodecs, UppercaseASCII, Tree

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

    @pytest.mark.parametrize("decoder", ourcodecs)
    def test_totality(self, decoder):
        """ Every bytestring can decoded """
        returned = ""
        for bs in self.bytestrings:
            returned = decoder.decode(bs)
            if not isinstance(returned, str):
                break
        assert isinstance(returned, str)

    @pytest.mark.skip()
    @pytest.mark.parametrize("codec", ourcodecs)
    def test_injective_decoding(self, codec):
        """ x != y -> decode(x) != decode(y) for all bytestrings x, y """
        inverse_graph = dict()
        for bs in self.bytestrings:
            d = codec.decode(bs)
            if d in inverse_graph:
                raise AssertionError(
                    "Injective property for {0} failed beause decode({1}) = decode({2}) = {3}".format(codec.__name__,
                                                                                                      bs,
                                                                                                      inverse_graph[
                                                                                                          d], d))
            inverse_graph[d] = bs

    @pytest.mark.skip()
    @pytest.mark.parametrize("codec", ourcodecs)
    def test_left_invertibility(self, codec):
        """ x == encode(decode(x)) for all bytestrings x """
        for bs in self.bytestrings:
            d = codec.decode(bs)
            e = codec.encode(d)
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
    (b'AbCD',
     ([b'A', b'b', b'C', b'D'], ["A", "B", "C", "D"], {(0,): {(0,)}, (1,): {(1,)}, (2,): {(2,)}, (3,): {(3,)}})),
])
def test_mapping_UppercaseASCII(bytestr, expected):
    b, s, f = UppercaseASCII.correspondence(bytestr)
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
        #([], ValueError),
        ([b''], 1),
        ([b'', b'a'], 2),
        ([b'', [b'a']], 2),
        ([b'', [b'a', b'bc']], 2),
    ])
    def test_len(self, arg, expected):
        if expected is ValueError:
            with pytest.raises(ValueError):
                Tree(arg)
        else:
            assert len(Tree(arg)) == expected

    @pytest.mark.parametrize("arg, expected", [
        ([b'abc'], "(b'abc')"),
        (['abc'], "('abc')"),
        (['abc', 'edf'], "('abc','edf')"),
        (['abc', ['ed', 'f']], "('abc',('ed','f'))"),
        (['a', [['c', 'd'], 'e'], 'b'], "('a',(('c','d'),'e'),'b')"),
    ])
    def test_str(self, arg, expected):
        t = Tree(arg)
        assert str(t) == expected

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
        [b'a', [[b'c', b'd']], b'b'],
        [b'a', [[b'c', b'd'], b'e'], b'b'],
    ])
    def test_list(self, expected):
        returned = Tree(expected).list()
        assert returned == expected

    @pytest.mark.parametrize("arg, expected", [
        ([b'a'], (0,)),
        ([b'ab', b'c'], (0, 1)),
        ([[b'hoy'], b'ab', b'c'], (0, 1, 2)),
        ([[b'hoy', b'yo'], b'ab', b'c'], (0, 2, 3)),
        ([[b'hoy', b'yo'], b'ab', [b'oy', b'yoh', b's'], b'c'], (0, 2, 3, 6)),
    ])
    def test_offsets(self, arg, expected):
        t = Tree(arg)
        assert t.offsets() == expected

    def test_reel_in(self):
        assert Tree([b'a']).reel_in(0) == b'a'
        assert Tree([b'a', b'b']).reel_in(0) == b'a'
        assert Tree([b'a', b'b']).reel_in(1) == b'b'
        assert Tree([b'a', [b'c'], b'b']).reel_in(1, 0) == b'c'
        assert Tree([b'a', [b'c', b'd'], b'b']).reel_in(1, 0) == b'c'
        assert Tree([b'a', [b'c', b'd'], b'b']).reel_in(1, 1) == b'd'

    @pytest.mark.parametrize("arg, expected", [
        ([b''], [(0,)]),
        ([b'ab', b'cde'], [(0,), (1,)]),
        ([b'ab', [b'cde', b'f']], [(0,), (1, 0), (1, 1)]),
        ([b'ab', [[b'cde'], [b'f', b'gh']]], [(0,), (1, 0, 0), (1, 1, 0), (1, 1, 1)]),
        ([[b'ab'], [b'c', b'de']], [(0, 0), (1, 0), (1, 1)]),
    ])
    def test_leaf_indices(self, arg, expected):
        t = Tree(arg)
        returned = t.leaf_indices()
        assert returned == expected

    @pytest.mark.parametrize("arg, expected", [
        ([b''], [()]),
        ([b'ab', b'cde'], [()]),
        ([b'ab', [b'cde', b'f']], [(), (1,)]),
        ([b'ab', [[b'cde'], [b'f', b'gh']]], [(), (1, 0), (1, 1)]),
        ([[b'ab'], [b'c', b'de']], [(0,), (1,)]),
    ])
    def test_leaf_parent_indices(self, arg, expected):
        t = Tree(arg)
        returned = t.leaf_parent_indices()
        assert returned == expected

    @pytest.mark.parametrize("arg, expected", [
#        ([b''], {(0,): (0,)}),
#        ([b'ab', b'cde'], {(0,): (0,), (1,): (1,)}),
        ([b'ab', [b'cde', b'f']], {(0,): (0,), (1, 0): (1, 0), (1, 1): (1, 1)}),
    ])
    @pytest.mark.skip()
    def test_graph(self, arg, expected):
        t = Tree(arg)
        returned = t.graph()
        assert returned == expected

    @pytest.mark.parametrize("arg, expected", [
#        ([b''], {(0,): (0,)}),
#        ([b'ab', b'cde'], {(1,): (0,), (0,): (1,)}),
#        ([b'ab', [b'cde', b'f']], {(0,): (1,), (1, 0): (0, 1), (1, 1): (0, 0)}),
    ])
    def test_inversion_graph(self, arg, expected):
        t = Tree(arg)
        t.invert()
        returned = t.graph()
        assert returned == expected

    @pytest.mark.parametrize("obj", [
        ([b'']),
        (['']),
        (Tree([''])),
        (['ABC']),
        ([b'a', b'b']),
        ([b'a', [b'b', [b'c', b'd'], b'e']]),
    ])
    def test_is_treelike(self, obj):
        assert Tree.is_treelike(obj)

    @pytest.mark.parametrize("obj", [
        ([]),
        ([5]),
        ([b'a', 'b']),
        ([b'a', [b'b', [b'c', 'd'], b'e']]),
    ])
    def test_is_not_treelike(self, obj):
        assert not Tree.is_treelike(obj)

    @pytest.mark.parametrize("obj", [
        ([]),
        ([5]),
        ([b'a', 'b']),
        ([b'a', [b'b', [b'c', 'd'], b'e']]),
    ])
    @pytest.mark.skip()
    def test_init_raises(self, obj):
        with pytest.raises(ValueError):
            Tree(obj)

    @pytest.mark.parametrize("arg1, arg2", [
        ([b''], ['']),
        ([b''], ['ABC']),
        ([b'a', b'b'], ['A', 'B']),
        ([b'a', [b'b', [b'c', b'd'], b'e']], ['a', ['b', ['c', 'd'], 'e']]),
    ])
    def test_graphically_equals(self, arg1, arg2):
        t1 = Tree(arg1)
        t2 = Tree(arg2)
        assert t1.graphically_equals(t1)  # Reflexivity
        assert t1.graphically_equals(t2)
        assert t2.graphically_equals(t1)  # Symmetry

    @pytest.mark.parametrize("t1, t2", [
        (Tree([b'ab']), Tree([b'a', b'b'])),
        (Tree([b'a', [b'b', [b'c', b'd'], b'e']]), Tree(['a', ['b', ['c', 'd', 'e'], 'f']])),
        (Tree([b'a', [b'b', [b'c', b'd'], b'e']]), Tree(['a', ['b', ['c', 'd', 'e']]])),
    ])
    def test_graphically_not_equals(self, t1, t2):
        assert not t1.graphically_equals(t2)
        assert not t2.graphically_equals(t1)  # Symmetry

    @pytest.mark.parametrize("arg, expected", [
        ([b'ab'], [b'ab']),
        ([b'ab', b'c'], [b'c', b'ab']),
        ([b'ab', [b'c', b'de'], b'f'], [b'f', [b'de', b'c'], b'ab']),
    ])
    @pytest.mark.skip()
    def test_invert(self, arg, expected):
        t = Tree(arg)
        t.invert()
        assert t.deeply_equals(Tree(expected))
        t.invert()
        assert t.deeply_equals(Tree(arg))

    @pytest.mark.parametrize("content, fn, expected", [
        ([b'Sebelino'], bytes.upper, Tree([b'SEBELINO'])),
        ([b'abc', [b'dEf', b'gh']], bytes.upper, Tree([b'ABC', [b'DEF', b'GH']])),
        ([b'abc', [b'dEf', b'gh']], bytes.decode, Tree(['abc', ['dEf', 'gh']])),
    ])
    def test_map(self, content, fn, expected):
        t = Tree(content)
        t2 = t.map(fn)
        assert t2 == expected

    @pytest.mark.parametrize("content, expected", [
        ([''], "('':0)"),
        ([b''], "(b'':0)"),
        (['ab', ['hey', 'yo']], "('ab':0,('hey':1,'yo':2):1)"),
        (['ab', ['hey', 'yo'], 'c'], "('ab':0,('hey':1,'yo':2):1,'c':3)"),
    ])
    @pytest.mark.skip()
    def test_repr(self, content, expected):
        assert repr(Tree(content)) == expected

    @pytest.mark.parametrize("t1, t2", [
        (Tree(['']), Tree([''])),
        #(Tree([''], _position=1), Tree([''], _position=1)),
        (Tree(['', ['abc', 'de']]), Tree(['', ['abc', 'de']])),
    ])
    def test_eq(self, t1, t2):
        assert t1 == t2

    @pytest.mark.parametrize("t1, t2", [
        (Tree(['']), Tree([b''])),
        #(Tree([''], _position=1), Tree([''])),
        (Tree(['', ['abc', 'de']]), Tree([b'', [b'abc', b'de']])),
    ])
    def test_neq(self, t1, t2):
        assert t1 != t2
