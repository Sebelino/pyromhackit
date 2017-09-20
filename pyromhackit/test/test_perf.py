#!/usr/bin/env python

import os
import pytest

from pyromhackit.selection import Selection

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

    def test_exclude_4000_times(self, benchmark):
        benchmark(self.exclude_n_times, self.v, 4000)


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

    def test_include_4000_times(self, benchmark):
        benchmark(self.include_n_times, self.v, 4000)


class TestSliceIndex(object):
    def setup(self):
        self.v = Selection(universe=slice(0, 2 * 10000),
                           revealed=[slice(2 * i, 2 * i + 1) for i in range(10000)])

    @staticmethod
    def slice_index_n_times(selection, n):
        for i in range(0, n):
            selection._slice_index(2 * i)

    def test_slice_index_1000(self, benchmark):
        benchmark(self.slice_index_n_times, self.v, 1000)

    def test_slice_index_2000(self, benchmark):
        benchmark(self.slice_index_n_times, self.v, 2000)

    def test_slice_index_4000(self, benchmark):
        benchmark(self.slice_index_n_times, self.v, 4000)
