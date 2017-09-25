#!/usr/bin/env python

import os
import pytest

from pyromhackit.selection import Selection
from pyromhackit.stringsearch.identify import EnglishDictionaryBasedIdentifier

package_dir = os.path.dirname(os.path.abspath(__file__))


class TestExclude(object):
    def setup(self):
        self.v = Selection(universe=slice(0, 100000))

    @staticmethod
    def exclude_n_times(selection, n):
        # revealed = [(0, 1), (2, 3), ..., (n-2, n-1)]
        for i in range(0, n):
            selection.exclude(2 * i + 1, 2 * i + 2)

    def test_exclude_500_times(self, benchmark):
        benchmark(self.exclude_n_times, self.v, 500)

    def test_exclude_1000_times(self, benchmark):
        benchmark(self.exclude_n_times, self.v, 1000)

    def test_exclude_2000_times(self, benchmark):
        benchmark(self.exclude_n_times, self.v, 2000)


class TestInclude(object):
    def setup(self):
        self.v = Selection(universe=slice(0, 100000), revealed=[])

    @staticmethod
    def include_n_times(selection, n):
        # revealed = [(0, 1), (2, 3), ..., (n-2, n-1)]
        for i in range(0, n):
            selection.include(2 * i, 2 * i + 1)

    def test_include_500_times(self, benchmark):
        benchmark(self.include_n_times, self.v, 500)

    def test_include_1000_times(self, benchmark):
        benchmark(self.include_n_times, self.v, 1000)

    def test_include_2000_times(self, benchmark):
        benchmark(self.include_n_times, self.v, 2000)


class TestSliceIndex(object):
    def setup(self):
        self.v = Selection(universe=slice(0, 2 * 10000),
                           revealed=[slice(2 * i, 2 * i + 1) for i in range(10000)])

    @staticmethod
    def slice_index_n_times(selection, n):
        for i in range(0, n):
            selection._slice_index(2 * i)

    def test_slice_index_500(self, benchmark):
        benchmark(self.slice_index_n_times, self.v, 500)

    def test_slice_index_1000(self, benchmark):
        benchmark(self.slice_index_n_times, self.v, 1000)

    def test_slice_index_2000(self, benchmark):
        benchmark(self.slice_index_n_times, self.v, 2000)


class TestComplement(object):
    def test_complement_500(self, benchmark):
        v = Selection(universe=slice(0, 2 * 500),
                      revealed=[slice(2 * i, 2 * i + 1) for i in range(500)])
        benchmark(v.complement)

    def test_complement_1000(self, benchmark):
        v = Selection(universe=slice(0, 2 * 1000),
                      revealed=[slice(2 * i, 2 * i + 1) for i in range(1000)])
        benchmark(v.complement)

    def test_complement_2000(self, benchmark):
        v = Selection(universe=slice(0, 2 * 2000),
                      revealed=[slice(2 * i, 2 * i + 1) for i in range(2000)])
        benchmark(v.complement)


class TestPreviousSlice(object):
    def setup(self):
        self.v = Selection(universe=slice(0, 2 * 10000),
                           revealed=[slice(2 * i, 2 * i + 1) for i in range(10000)])

    @staticmethod
    def covered_previous_slice_n_times(selection, n):
        for i in range(1, n):
            selection._previous_slice(slice(2 * i, 2 * i + 1))

    @staticmethod
    def revealed_previous_slice_n_times(selection, n):
        for i in range(0, n):
            selection._previous_slice(slice(2 * i + 1, 2 * i + 2))

    def test_previous_slice_50_covered(self, benchmark):
        benchmark(self.covered_previous_slice_n_times, self.v, 50)

    def test_previous_slice_100_covered(self, benchmark):
        benchmark(self.covered_previous_slice_n_times, self.v, 100)

    def test_previous_slice_200_covered(self, benchmark):
        benchmark(self.covered_previous_slice_n_times, self.v, 200)

    def test_previous_slice_50_revealed(self, benchmark):
        benchmark(self.revealed_previous_slice_n_times, self.v, 50)

    def test_previous_slice_100_revealed(self, benchmark):
        benchmark(self.revealed_previous_slice_n_times, self.v, 100)

    def test_previous_slice_200_revealed(self, benchmark):
        benchmark(self.revealed_previous_slice_n_times, self.v, 200)


class TestEnglishDictionaryBasedIdentifier(object):
    def setup(self):
        self.identifier = EnglishDictionaryBasedIdentifier(tolerated_char_count=0)
        #self.corpus = lorem.ipsum()[:1000]
        self.corpus = ("hello " * 1000)[:1000]

    def test_str2selection_2pow0(self, benchmark):
        corpus = self.corpus * 2**0
        benchmark(self.identifier.str2selection, corpus)

    def test_str2selection_2pow1(self, benchmark):
        corpus = self.corpus * 2**1
        benchmark(self.identifier.str2selection, corpus)

    def test_str2selection_2pow2(self, benchmark):
        corpus = self.corpus * 2**2
        benchmark(self.identifier.str2selection, corpus)

    def test_str2selection_2pow3(self, benchmark):
        corpus = self.corpus * 2**3
        benchmark(self.identifier.str2selection, corpus)

    def test_str2selection_2pow4(self, benchmark):
        corpus = self.corpus * 2**4
        benchmark(self.identifier.str2selection, corpus)
