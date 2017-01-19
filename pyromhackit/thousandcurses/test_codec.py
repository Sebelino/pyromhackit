#!/usr/bin/env python

"""
Tests for checking the bijective property of codecs.
"""

from nose.tools import assert_equal, assert_not_equal, assert_true
import unittest
import os

from .codec import names

package_dir = os.path.dirname(os.path.abspath(__file__))

class TestBijection(object):

    @classmethod
    def setup_class(cls):
        cls.bytestrings = [bytes([i]) for i in range(2**8)]
        cls.strings = [chr(i) for i in range(2**8)]

    def test_totality(cls):
        """ Every bytestring can decoded """
        for name in names:
            cdc = names[name]
            returned = ""
            for bs in cls.bytestrings:
                returned = cdc.decode(bs)
                if not isinstance(returned, str):
                    break
            yield assert_true, isinstance(returned, str)

    def test_injective_decoding(cls):
        """ x != y -> decode(x) != decode(y) for all bytestrings x, y """
        for name in names:
            cdc = names[name]
            inverse_graph = dict()
            for bs in cls.bytestrings:
                d = cdc.decode(bs)
                if d in inverse_graph:
                    raise AssertionError("Injective property for {0} failed beause decode({1}) = decode({2}) = {3}".format(name, bs, inverse_graph[d], d))
                inverse_graph[d] = bs

    @unittest.skip("TODO")
    def test_left_invertibility(cls):
        """ x == encode(decode(x)) for all bytestrings x """
        for name in names:
            cdc = names[name]
            for bs in cls.bytestrings:
                d = cdc.decode(bs)
                e = cdc.encode(d)
                yield assert_equal, e, bs

    @unittest.skip("TODO")
    def test_right_invertibility(cls):
        """ x == decode(encode(x)) for all strings x """
