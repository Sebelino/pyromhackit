#!/usr/bin/env python

import os
import pytest

from pyromhackit.selection import Selection

package_dir = os.path.dirname(os.path.abspath(__file__))


def test_err():
    with pytest.raises(AssertionError):
        Selection(slice(0, 0))


def test_simple():
    v = Selection(slice(0, 10))
    assert v.revealed == [slice(0, 10)]


class TestCoverup(object):
    def setup(self):
        self.v = Selection(slice(0, 10))
        self.v.revealed = [slice(3, 7)]  # Poor man's mocking

    def test_lt_a_lt_a(self):
        self.v.coverup(1, 2)
        assert self.v.revealed == [slice(3, 7)]

    def test_lt_a_eq_a(self):
        self.v.coverup(1, 3)
        assert self.v.revealed == [slice(3, 7)]

    def test_lt_a_in_ab(self):
        self.v.coverup(1, 5)
        assert self.v.revealed == [slice(5, 7)]

    def test_lt_a_eq_b(self):
        self.v.coverup(1, 7)
        assert self.v.revealed == []

    def test_lt_a_gt_b(self):
        self.v.coverup(1, 8)
        assert self.v.revealed == []

    def test_eq_a_in_ab(self):
        self.v.coverup(3, 5)
        assert self.v.revealed == [slice(5, 7)]

    def test_eq_a_eq_b(self):
        self.v.coverup(3, 7)
        assert self.v.revealed == []

    def test_eq_a_gt_b(self):
        self.v.coverup(3, 8)
        assert self.v.revealed == []

    def test_in_ab_in_ab(self):
        self.v.coverup(4, 6)
        assert self.v.revealed == [slice(3, 4), slice(6, 7)]

    def test_in_ab_eq_b(self):
        self.v.coverup(4, 7)
        assert self.v.revealed == [slice(3, 4)]

    def test_in_ab_gt_b(self):
        self.v.coverup(4, 8)
        assert self.v.revealed == [slice(3, 4)]

    def test_eq_b_gt_b(self):
        self.v.coverup(7, 8)
        assert self.v.revealed == [slice(3, 7)]

    def test_gt_b_gt_b(self):
        self.v.coverup(8, 9)
        assert self.v.revealed == [slice(3, 7)]


class TestReveal(object):
    def setup(self):
        self.v = Selection(slice(0, 10))
        self.v.revealed = [slice(3, 7)]  # Poor man's mocking

    def test_lt_a_lt_a(self):
        self.v.reveal(1, 2)
        assert self.v.revealed == [slice(1, 2), slice(3, 7)]

    def test_lt_a_eq_a(self):
        self.v.reveal(1, 3)
        assert self.v.revealed == [slice(1, 7)]

    def test_lt_a_in_ab(self):
        self.v.reveal(1, 5)
        assert self.v.revealed == [slice(1, 7)]

    def test_lt_a_eq_b(self):
        self.v.reveal(1, 7)
        assert self.v.revealed == [slice(1, 7)]

    def test_lt_a_gt_b(self):
        self.v.reveal(1, 8)
        assert self.v.revealed == [slice(1, 8)]

    def test_eq_a_in_ab(self):
        self.v.reveal(3, 5)
        assert self.v.revealed == [slice(3, 7)]

    def test_eq_a_eq_b(self):
        self.v.reveal(3, 7)
        assert self.v.revealed == [slice(3, 7)]

    def test_eq_a_gt_b(self):
        self.v.reveal(3, 8)
        assert self.v.revealed == [slice(3, 8)]

    def test_in_ab_in_ab(self):
        self.v.reveal(4, 6)
        assert self.v.revealed == [slice(3, 7)]

    def test_in_ab_eq_b(self):
        self.v.reveal(4, 7)
        assert self.v.revealed == [slice(3, 7)]

    def test_in_ab_gt_b(self):
        self.v.reveal(4, 8)
        assert self.v.revealed == [slice(3, 8)]

    def test_eq_b_gt_b(self):
        self.v.reveal(7, 8)
        assert self.v.revealed == [slice(3, 8)]

    def test_gt_b_gt_b(self):
        self.v.reveal(8, 9)
        assert self.v.revealed == [slice(3, 7), slice(8, 9)]
