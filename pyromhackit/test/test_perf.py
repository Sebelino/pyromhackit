#!/usr/bin/env python

import os
import pytest

from pyromhackit.selection import Selection

package_dir = os.path.dirname(os.path.abspath(__file__))




class TestCoverup(object):
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

