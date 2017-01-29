#!/usr/bin/env python

"""
Tests for checking the bijective property of codecs.
"""

import pytest
import os

from .codec import codecnames, decodernames

package_dir = os.path.dirname(os.path.abspath(__file__))


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
