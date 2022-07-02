#!/usr/bin/env python

import pytest

from pyromhackit.gslice.selection import Selection


class TestExclude(object):
    def setup(self):
        self.v = Selection(universe=slice(0, 100000))

    @staticmethod
    def exclude_n_times(selection, n):
        # revealed = [(0, 1), (2, 3), ..., (2n-2, 2n-1), (2n, 100000)]
        for i in range(0, n):
            selection.exclude(2 * i + 1, 2 * i + 2)

    def test_exclude_2pow0_times(self, benchmark):
        benchmark(self.exclude_n_times, self.v, 500 * 2 ** 0)

    def test_exclude_2pow1_times(self, benchmark):
        benchmark(self.exclude_n_times, self.v, 500 * 2 ** 1)

    def test_exclude_2pow2_times(self, benchmark):
        benchmark(self.exclude_n_times, self.v, 500 * 2 ** 2)


class TestInclude(object):
    def setup(self):
        self.v = Selection(universe=slice(0, 100000), revealed=[])

    @staticmethod
    def include_n_times(selection, n):
        # revealed = [(0, 1), (2, 3), ..., (n-2, n-1)]
        for i in range(0, n):
            selection.include(2 * i, 2 * i + 1)

    def test_include_2pow0_times(self, benchmark):
        benchmark(self.include_n_times, self.v, 500 * 2 ** 0)

    def test_include_2pow1_times(self, benchmark):
        benchmark(self.include_n_times, self.v, 500 * 2 ** 1)

    def test_include_2pow2_times(self, benchmark):
        benchmark(self.include_n_times, self.v, 500 * 2 ** 2)


class TestSubslice(object):
    def setup(self):
        self.without_gaps = Selection(universe=slice(0, 100000))
        self.with_gaps = Selection(universe=slice(0, 100000), intervals=list(range(100000 + 1)))

    @staticmethod
    def subslice_n_times(selection, n):
        for i in range(0, n):
            selection.subslice(2 * i, 2 * i + 1)

    def test_without_gaps(self, benchmark):
        benchmark(self.subslice_n_times, self.without_gaps, 2 ** 2)

    def test_with_gaps(self, benchmark):
        benchmark(self.subslice_n_times, self.with_gaps, 2 ** 2)


class TestIncludePartiallyFromLeft(object):
    def setup(self):
        self.v = Selection(universe=slice(0, 100000), revealed=[])

    @staticmethod
    def do_n_times(selection, n):
        # Include partially from right (0, 1), (1, 2), (2, 3), ...
        for i in range(0, n):
            selection._include_partially_from_left(2 * i, 2 * i + 1, 1)

    def test_2pow0_times(self, benchmark):
        benchmark(self.do_n_times, self.v, 500 * 2 ** 0)

    def test_2pow1_times(self, benchmark):
        benchmark(self.do_n_times, self.v, 500 * 2 ** 1)

    def test_2pow2_times(self, benchmark):
        benchmark(self.do_n_times, self.v, 500 * 2 ** 2)

    def test_2pow3_times(self, benchmark):
        benchmark(self.do_n_times, self.v, 500 * 2 ** 3)


class TestIncludePartiallyFromRight(object):
    def setup(self):
        self.v = Selection(universe=slice(0, 100000), revealed=[])

    @staticmethod
    def do_n_times(selection, n):
        # Include partially from right (0, 1), (1, 2), (2, 3), ...
        for i in range(0, n):
            selection._include_partially_from_right(2 * i, 2 * i + 1, 1)

    def test_2pow0_times(self, benchmark):
        benchmark(self.do_n_times, self.v, 500 * 2 ** 0)

    def test_2pow1_times(self, benchmark):
        benchmark(self.do_n_times, self.v, 500 * 2 ** 1)

    def test_2pow2_times(self, benchmark):
        benchmark(self.do_n_times, self.v, 500 * 2 ** 2)

    def test_2pow3_times(self, benchmark):
        benchmark(self.do_n_times, self.v, 500 * 2 ** 3)


class TestIncludePartially(object):
    def setup(self):
        self.v = Selection(universe=slice(0, 100000), revealed=[])

    @staticmethod
    def do_n_times(selection, n):
        for i in range(0, n):
            selection.include_partially(2 * i, 2 * i + 1, 1)

    def test_include_partially_2pow0(self, benchmark):
        benchmark(self.do_n_times, self.v, 500 * 2 ** 0)

    def test_include_partially_2pow1(self, benchmark):
        benchmark(self.do_n_times, self.v, 500 * 2 ** 1)

    def test_include_partially_2pow2(self, benchmark):
        benchmark(self.do_n_times, self.v, 500 * 2 ** 2)


class TestComplement(object):
    def test_complement_1000(self, benchmark):
        v = Selection(universe=slice(0, 2 * 1000),
                      revealed=[slice(2 * i, 2 * i + 1) for i in range(1000)])
        benchmark(v.complement)

    def test_complement_2000(self, benchmark):
        v = Selection(universe=slice(0, 2 * 2000),
                      revealed=[slice(2 * i, 2 * i + 1) for i in range(2000)])
        benchmark(v.complement)

    def test_complement_4000(self, benchmark):
        v = Selection(universe=slice(0, 2 * 4000),
                      revealed=[slice(2 * i, 2 * i + 1) for i in range(4000)])
        benchmark(v.complement)

    def test_complement_8000(self, benchmark):
        v = Selection(universe=slice(0, 2 * 8000),
                      revealed=[slice(2 * i, 2 * i + 1) for i in range(8000)])
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

    @pytest.mark.skip()
    def test_previous_slice_50_covered(self, benchmark):
        benchmark(self.covered_previous_slice_n_times, self.v, 50)

    @pytest.mark.skip()
    def test_previous_slice_100_covered(self, benchmark):
        benchmark(self.covered_previous_slice_n_times, self.v, 100)

    @pytest.mark.skip()
    def test_previous_slice_200_covered(self, benchmark):
        benchmark(self.covered_previous_slice_n_times, self.v, 200)

    @pytest.mark.skip()
    def test_previous_slice_50_revealed(self, benchmark):
        benchmark(self.revealed_previous_slice_n_times, self.v, 50)

    @pytest.mark.skip()
    def test_previous_slice_100_revealed(self, benchmark):
        benchmark(self.revealed_previous_slice_n_times, self.v, 100)

    @pytest.mark.skip()
    def test_previous_slice_200_revealed(self, benchmark):
        benchmark(self.revealed_previous_slice_n_times, self.v, 200)
