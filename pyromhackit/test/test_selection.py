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


def test_init2():
    v = Selection(slice(0, 10), revealed=[slice(3, 5)])
    assert v.revealed == [slice(3, 5)]


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


def test_empty_revealed():
    v = Selection(slice(0, 10))
    v.coverup(0, 10)
    assert v.revealed == []
    v.reveal(3, 7)
    assert v.revealed == [slice(3, 7)]


class TestIndexing(object):
    def setup(self):
        self.v = Selection(slice(0, 10))
        self.v.revealed = [slice(3, 7)]  # Poor man's mocking

    def test_index(self):
        assert self.v.index(5) == slice(3, 7)

    @pytest.mark.parametrize("pindex", [2, 7])
    def test_index_raises(self, pindex):
        with pytest.raises(ValueError):
            self.v.index(pindex)

    @pytest.mark.parametrize("vindex, expected", [
        (0, 3),
        (3, 6),
    ])
    def test_v2p(self, vindex, expected):
        assert self.v.virtual2physical(vindex) == expected

    @pytest.mark.parametrize("vindex, expected", [
        (-1, IndexError),
        (4, IndexError),
    ])
    def test_v2p_raises(self, vindex, expected):
        with pytest.raises(expected):
            self.v.virtual2physical(vindex)

    @pytest.mark.parametrize("pindex, expected", [
        (3, 0),
        (6, 3),
    ])
    def test_p2v(self, pindex, expected):
        assert self.v.physical2virtual(pindex) == expected

    @pytest.mark.parametrize("pindex, expected", [
        (-1, IndexError),
        (2, IndexError),
        (7, IndexError),
        (10, IndexError),
    ])
    def test_p2v_raises(self, pindex, expected):
        with pytest.raises(expected):
            self.v.physical2virtual(pindex)

    def test_getitem(self):
        assert self.v[0] == 3

    def test_select(self):
        content = "HelloWorld"
        assert self.v.select(content) == "loWo"

    @pytest.mark.parametrize("vslice, expected", [
        (slice(0, None), Selection(slice(0, 10), [slice(3, 7)])),
        (slice(None, 4), Selection(slice(0, 10), [slice(3, 7)])),
        (slice(None, None), Selection(slice(0, 10), [slice(3, 7)])),
        (slice(1, 3), Selection(slice(0, 10), [slice(4, 6)])),
        (slice(0, 0), Selection(slice(0, 10), [])),
        (slice(None, 5), Selection(slice(0, 10), [slice(3, 7)])),
        (slice(None, 9), Selection(slice(0, 10), [slice(3, 7)])),
        (slice(None, 15), Selection(slice(0, 10), [slice(3, 7)])),
        (slice(4, 5), Selection(slice(0, 10), [])),
        (slice(4, 9), Selection(slice(0, 10), [])),
        (slice(4, 15), Selection(slice(0, 10), [])),
    ])
    def test_v2p_selection(self, vslice, expected):  # TODO negatives; slices (a,b) where a > b
        assert self.v.virtual2physicalselection(vslice) == expected

