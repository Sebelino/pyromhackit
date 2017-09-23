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


class TestGapSliceGap(object):
    def setup(self):
        self.v = Selection(universe=slice(0, 10), revealed=[slice(3, 7)])

    """ Selection.exclude """

    def test_exclude_lt_a_lt_a(self):
        self.v.exclude(1, 2)
        assert self.v.revealed == [slice(3, 7)]

    def test_exclude_lt_a_eq_a(self):
        self.v.exclude(1, 3)
        assert self.v.revealed == [slice(3, 7)]

    def test_exclude_lt_a_in_ab(self):
        self.v.exclude(1, 5)
        assert self.v.revealed == [slice(5, 7)]

    def test_exclude_lt_a_eq_b(self):
        self.v.exclude(1, 7)
        assert self.v.revealed == []

    def test_exclude_lt_a_gt_b(self):
        self.v.exclude(1, 8)
        assert self.v.revealed == []

    def test_exclude_eq_a_eq_a(self):
        self.v.exclude(3, 3)
        assert self.v.revealed == [slice(3, 7)]

    def test_exclude_eq_a_in_ab(self):
        self.v.exclude(3, 5)
        assert self.v.revealed == [slice(5, 7)]

    def test_exclude_eq_a_eq_b(self):
        self.v.exclude(3, 7)
        assert self.v.revealed == []

    def test_exclude_eq_a_gt_b(self):
        self.v.exclude(3, 8)
        assert self.v.revealed == []

    def test_exclude_in_ab_in_ab(self):
        self.v.exclude(4, 6)
        assert self.v.revealed == [slice(3, 4), slice(6, 7)]

    def test_exclude_in_ab_eq_b(self):
        self.v.exclude(4, 7)
        assert self.v.revealed == [slice(3, 4)]

    def test_exclude_in_ab_gt_b(self):
        self.v.exclude(4, 8)
        assert self.v.revealed == [slice(3, 4)]

    def test_exclude_eq_b_eq_b(self):
        self.v.exclude(7, 7)
        assert self.v.revealed == [slice(3, 7)]

    def test_exclude_eq_b_gt_b(self):
        self.v.exclude(7, 8)
        assert self.v.revealed == [slice(3, 7)]

    def test_exclude_gt_b_gt_b(self):
        self.v.exclude(8, 9)
        assert self.v.revealed == [slice(3, 7)]

    def test_exclude_in_ab_eq_max(self):
        self.v.exclude(4, 10)
        assert self.v.revealed == [slice(3, 4)]

    def test_exclude_in_ab_gt_max(self):
        self.v.exclude(4, 11)
        assert self.v.revealed == [slice(3, 4)]

    def test_exclude_eq_min_eq_min(self):
        self.v.exclude(0, 0)
        assert self.v.revealed == [slice(3, 7)]

    def test_exclude_eq_min_eq_b(self):
        self.v.exclude(0, 7)
        assert self.v.revealed == []

    def test_exclude_eq_max_eq_max(self):
        self.v.exclude(10, 10)
        assert self.v.revealed == [slice(3, 7)]

    """ Selection.include """

    def test_include_lt_a_lt_a(self):
        self.v.include(1, 2)
        assert self.v.revealed == [slice(1, 2), slice(3, 7)]

    def test_include_lt_a_eq_a(self):
        self.v.include(1, 3)
        assert self.v.revealed == [slice(1, 7)]

    def test_include_lt_a_in_ab(self):
        self.v.include(1, 5)
        assert self.v.revealed == [slice(1, 7)]

    def test_include_lt_a_eq_b(self):
        self.v.include(1, 7)
        assert self.v.revealed == [slice(1, 7)]

    def test_include_lt_a_gt_b(self):
        self.v.include(1, 8)
        assert self.v.revealed == [slice(1, 8)]

    def test_include_eq_a_eq_a(self):
        self.v.include(3, 3)
        assert self.v.revealed == [slice(3, 7)]

    def test_include_eq_a_in_ab(self):
        self.v.include(3, 5)
        assert self.v.revealed == [slice(3, 7)]

    def test_include_eq_a_eq_b(self):
        self.v.include(3, 7)
        assert self.v.revealed == [slice(3, 7)]

    def test_include_eq_a_gt_b(self):
        self.v.include(3, 8)
        assert self.v.revealed == [slice(3, 8)]

    def test_include_in_ab_in_ab(self):
        self.v.include(4, 6)
        assert self.v.revealed == [slice(3, 7)]

    def test_include_in_ab_eq_b(self):
        self.v.include(4, 7)
        assert self.v.revealed == [slice(3, 7)]

    def test_include_in_ab_gt_b(self):
        self.v.include(4, 8)
        assert self.v.revealed == [slice(3, 8)]

    def test_include_eq_b_eq_b(self):
        self.v.include(7, 7)
        assert self.v.revealed == [slice(3, 7)]

    def test_include_eq_b_gt_b(self):
        self.v.include(7, 8)
        assert self.v.revealed == [slice(3, 8)]

    def test_include_gt_b_gt_b(self):
        self.v.include(8, 9)
        assert self.v.revealed == [slice(3, 7), slice(8, 9)]

    def test_include_in_ab_eq_max(self):
        self.v.include(4, 10)
        assert self.v.revealed == [slice(3, 10)]

    def test_include_in_ab_gt_max(self):
        self.v.include(4, 11)
        assert self.v.revealed == [slice(3, 10)]

    def test_include_eq_min_eq_min(self):
        self.v.include(0, 0)
        assert self.v.revealed == [slice(3, 7)]

    def test_include_eq_max_eq_max(self):
        self.v.include(10, 10)
        assert self.v.revealed == [slice(3, 7)]

    """ Misc """

    @pytest.mark.parametrize("pindex, expected", [
        (0, 0),
        (2, 0),
        (7, 1),
    ])
    def test_gap_index(self, pindex, expected):
        assert self.v._gap_index(pindex) == expected


class TestMiddleGap(object):
    def setup(self):
        self.v = Selection(universe=slice(0, 10), revealed=[slice(0, 3), slice(7, 10)])

    def test_eq_min_in_ab(self):
        self.v.exclude(0, 1)
        assert self.v.revealed == [slice(1, 3), slice(7, 10)]


def test_exclude_all_and_include():
    v = Selection(slice(0, 10))
    v.exclude(0, 10)
    assert v.revealed == []
    v.include(3, 7)
    assert v.revealed == [slice(3, 7)]


class TestIndexing(object):
    def setup(self):
        self.v = Selection(slice(0, 10))
        self.v.exclude(0, 3)
        self.v.exclude(7, 10)

    def test_index(self):
        assert self.v._index(5) == slice(3, 7)

    @pytest.mark.parametrize("pindex", [2, 7])
    def test_index_raises(self, pindex):
        with pytest.raises(IndexError):
            self.v._index(pindex)

    @pytest.mark.parametrize("vindex, expected", [
        (0, 3),
        (3, 6),
        (-1, 6),
    ])
    def test_v2p(self, vindex, expected):
        assert self.v.virtual2physical(vindex) == expected

    @pytest.mark.parametrize("vindex, expected", [
        # (-1, IndexError),
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
        (slice(None, 3), Selection(slice(0, 10), [slice(3, 6)])),
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
        (slice(-2, None), Selection(slice(0, 10), [slice(5, 7)])),
        (slice(-2, -1), Selection(slice(0, 10), [slice(5, 6)])),
    ])
    def test_v2p_selection(self, vslice, expected):  # TODO negatives; slices (a,b) where a > b
        assert self.v.virtual2physicalselection(vslice) == expected


class TestFullyExcluded(object):
    def setup(self):
        self.v = Selection(universe=slice(0, 10), revealed=[])

    def test_exclude_in_universe_eq_max(self):
        self.v.exclude(5, 10)
        assert self.v.revealed == []

    def test_include_len_eq_min_eq_max(self):
        self.v.include(0, 10)
        assert len(self.v) == 10

    def test_index_raises(self):
        with pytest.raises(IndexError):
            self.v._index(0)

    def test_v2p_raises(self):
        with pytest.raises(IndexError):
            self.v.virtual2physical(0)

    def test_p2v_raises(self):
        with pytest.raises(IndexError):
            self.v.physical2virtual(0)

    def test_getitem(self):
        with pytest.raises(IndexError):
            self.v[0]

    def test_select(self):
        content = "HelloWorld"
        assert self.v.select(content) == ""

    @pytest.mark.parametrize("vslice, expected", [
        (slice(0, None), Selection(slice(0, 10), [])),
        (slice(None, 3), Selection(slice(0, 10), [])),
        (slice(None, 4), Selection(slice(0, 10), [])),
        (slice(None, None), Selection(slice(0, 10), [])),
        (slice(1, 3), Selection(slice(0, 10), [])),
        (slice(0, 0), Selection(slice(0, 10), [])),
        (slice(None, 5), Selection(slice(0, 10), [])),
        (slice(None, 9), Selection(slice(0, 10), [])),
        (slice(None, 15), Selection(slice(0, 10), [])),
        (slice(4, 5), Selection(slice(0, 10), [])),
        (slice(4, 9), Selection(slice(0, 10), [])),
        (slice(4, 15), Selection(slice(0, 10), [])),
    ])
    def test_v2p_selection(self, vslice, expected):  # TODO negatives; slices (a,b) where a > b
        assert self.v.virtual2physicalselection(vslice) == expected


@pytest.mark.parametrize("revealed, expected", [
    ([], [slice(0, 10)]),
    ([slice(0, 10)], []),
    ([slice(0, 3)], [slice(3, 10)]),
    ([slice(3, 10)], [slice(0, 3)]),
    ([slice(0, 3), slice(5, 10)], [slice(3, 5)]),
    ([slice(0, 3), slice(5, 7)], [slice(3, 5), slice(7, 10)]),
    ([slice(1, 3), slice(5, 10)], [slice(0, 1), slice(3, 5)]),
    ([slice(1, 3), slice(5, 7)], [slice(0, 1), slice(3, 5), slice(7, 10)]),
])
def test_complement(revealed, expected):
    selection = Selection(universe=slice(0, 10), revealed=revealed)
    assert selection.complement().revealed == expected


@pytest.mark.parametrize("from_index, to_index, revealed, expected_revealed", [
    (9, 10, [slice(1, 9)], [slice(1, 10)]),
])
def test_include(from_index, to_index, revealed, expected_revealed):
    v = Selection(universe=slice(0, 10), revealed=revealed)
    v.include(from_index, to_index)
    assert v.revealed == expected_revealed


class TestThreeRevealedIntervals(object):
    def setup(self):
        self.v = Selection(universe=slice(0, 10), revealed=[slice(0, 2), slice(4, 6), slice(9, 10)])

    def test_exclude(self):
        self.v.exclude(2, None)
        assert self.v.revealed == [slice(0, 2)]

    @pytest.mark.parametrize("pindex, expected", [
        (0, 0),
        (1, 0),
        (4, 1),
        (5, 1),
        (9, 2),
    ])
    def test_slice_index(self, pindex, expected):
        assert self.v._slice_index(pindex) == expected

    @pytest.mark.parametrize("pindex", [
        2, 3, 6, 7, 8,
    ])
    def test_slice_index_raises(self, pindex):
        with pytest.raises(IndexError):
            self.v._slice_index(pindex)

    @pytest.mark.parametrize("pindex, expected", [
        (2, 0),
        (3, 0),
        (7, 1),
        (8, 1),
    ])
    def test_gap_index(self, pindex, expected):
        assert self.v._gap_index(pindex) == expected

    @pytest.mark.parametrize("from_index, to_index, expected_revealed", [
        (0, 10, [slice(0, 2), slice(4, 6), slice(9, 10)]),
        (None, None, [slice(0, 2), slice(4, 6), slice(9, 10)]),
    ])
    def test_subslice(self, from_index, to_index, expected_revealed):
        subsel = self.v.subslice(from_index, to_index)
        assert subsel.revealed == expected_revealed

    @pytest.mark.parametrize("from_index, to_index, expected", [
        (2, 3, [slice(0, 3), slice(4, 6), slice(9, 10)]),
        (1, 3, [slice(0, 3), slice(4, 6), slice(9, 10)]),
        (2, 4, [slice(0, 6), slice(9, 10)]),
        (8, 9, [slice(0, 2), slice(4, 6), slice(8, 10)]),
    ])
    def test_include(self, from_index, to_index, expected):
        self.v.include(from_index, to_index)
        assert self.v.revealed == expected

    def test_complement_universe(self):
        assert self.v.complement().universe == self.v.universe

    def test_complement_revealed(self):
        assert self.v.complement().revealed == [slice(2, 4), slice(6, 9)]

    def test_include_partially_from_left(self):
        self.v._include_partially_from_left(1, 9, 1)
        assert self.v.revealed == [slice(0, 3), slice(4, 6), slice(9, 10)]

    def test_include_partially_from_right(self):
        self.v._include_partially_from_right(1, 9, 1)
        assert self.v.revealed == [slice(0, 2), slice(4, 6), slice(8, 10)]

    def test_include_partially(self):
        self.v.include_partially(None, None, 1)
        assert self.v.revealed == [slice(0, 3), slice(4, 6), slice(8, 10)]

    @pytest.mark.parametrize("from_index, to_index, count, expected_revealed", [
        (None, None, 1, [slice(0, 7), slice(8, 10)]),
        (None, None, (1, 1), [slice(0, 7), slice(8, 10)]),
        (None, None, (1, 0), [slice(0, 2), slice(3, 6), slice(8, 10)]),
        (None, None, (0, 1), [slice(0, 3), slice(4, 7), slice(9, 10)]),
        (None, None, 2, [slice(0, 10)]),
    ])
    def test_include_expand(self, from_index, to_index, count, expected_revealed):
        self.v.include_expand(from_index, to_index, count)
        assert self.v.revealed == expected_revealed


def test_exclude():
    v = Selection(universe=slice(0, 10), revealed=[slice(3, 4), slice(6, 9)])
    v.exclude(4, 10)
    assert v.revealed == [slice(3, 4)]


@pytest.mark.parametrize("from_index, to_index, revealed, expected_revealed", [
    (0, 2, [slice(0, 2), slice(4, 6), slice(9, 10)], [slice(0, 2)]),
    (2, 4, [slice(3, 4), slice(6, 9)], [slice(3, 4)]),
])
def test_subslice(from_index, to_index, revealed, expected_revealed):
    v = Selection(universe=slice(0, 10), revealed=revealed)
    subsel = v.subslice(from_index, to_index)
    assert subsel.revealed == expected_revealed


def test_include_partially_from_right():
    v = Selection(universe=slice(0, 10), revealed=[slice(0, 3), slice(4, 6), slice(9, 10)])
    v._include_partially_from_right(2, 4, 1)
    assert v.revealed == [slice(0, 6), slice(9, 10)]


class TestThreeExcludedIntervals(object):
    def setup(self):
        self.v = Selection(universe=slice(0, 10), revealed=[slice(2, 4), slice(6, 9)])

    @pytest.mark.parametrize("pindex, expected", [
        (0, 0),
        (1, 0),
        (4, 1),
        (5, 1),
        (9, 2),
    ])
    def test_gap_index(self, pindex, expected):
        assert self.v._gap_index(pindex) == expected


    @pytest.mark.parametrize("from_index, to_index, expected", [
        (4, 5, [slice(2, 5), slice(6, 9)]),
        (4, 4, [slice(2, 4), slice(6, 9)]),
    ])
    def test_include(self, from_index, to_index, expected):
        self.v.include(from_index, to_index)
        assert self.v.revealed == expected

    def test_include_partially_from_right(self):
        self.v._include_partially_from_right(0, 2, 1)
        assert self.v.revealed == [slice(1, 4), slice(6, 9)]

    @pytest.mark.parametrize("from_index, to_index, count, expected_revealed", [
        (None, None, 1, [slice(1, 10)]),
        (None, None, (1, 1), [slice(1, 10)]),
        (None, None, (1, 0), [slice(1, 4), slice(5, 9)]),
        (None, None, (0, 1), [slice(2, 5), slice(6, 10)]),
        (None, None, 2, [slice(0, 10)]),
    ])
    def test_include_expand(self, from_index, to_index, count, expected_revealed):
        self.v.include_expand(from_index, to_index, count)
        assert self.v.revealed == expected_revealed


class TestNormalization(object):
    def setup(self):
        self.v = Selection(slice(0, 5))

    def test_include(self):
        self.v.include(1, 2)
        assert self.v.revealed == [slice(0, 5)]

    def test_exclude_and_include(self):
        self.v.exclude(1, 2)
        self.v.include(2, 3)
        assert self.v.revealed == [slice(0, 1), slice(2, 5)]


class TestVirtualExclusion(object):
    def setup(self):
        self.v = Selection(slice(0, 5))

    def test_exclude_virtual_cumulatively(self):
        self.v.exclude_virtual(1, 2)
        self.v.exclude_virtual(1, 2)
        assert self.v == Selection(universe=slice(0, 5), revealed=[slice(0, 1), slice(3, 5)])

    def test_exclude_virtual_and_include_virtual(self):
        self.v.exclude_virtual(1, 2)
        self.v.exclude_virtual(1, 2)
        self.v.include_virtual(0, 1)
        assert self.v == Selection(universe=slice(0, 5), revealed=[slice(0, 5)])

    def test_exclude_virtual_all(self):
        self.v.exclude_virtual(None, 7)
        assert self.v == Selection(universe=slice(0, 5), revealed=[])


class TestIncludePartially(object):
    def setup(self):
        self.v = Selection(slice(0, 10), revealed=[slice(0, 2), slice(7, 10)])

    def test_include_partially_lt_a_lt_a(self):
        self.v.include_partially(0, 1, 1)
        assert self.v.revealed == [slice(0, 2), slice(7, 10)]

    def test_include_partially_lt_a_eq_a(self):
        self.v.include_partially(1, 2, 1)
        assert self.v.revealed == [slice(0, 2), slice(7, 10)]

    def test_include_partially_lt_a_in_ab(self):
        self.v.include_partially(1, 5, 1)
        assert self.v.revealed == [slice(0, 3), slice(4, 5), slice(7, 10)]

    def test_include_partially_lt_a_eq_b(self):
        self.v.include_partially(1, 7, 1)
        assert self.v.revealed == [slice(0, 3), slice(6, 10)]

    def test_include_partially_lt_a_gt_b(self):
        self.v.include_partially(1, 8, 1)
        assert self.v.revealed == [slice(0, 3), slice(6, 10)]

    def test_include_partially_eq_a_in_ab(self):
        self.v.include_partially(2, 5, 1)
        assert self.v.revealed == [slice(0, 3), slice(4, 5), slice(7, 10)]

    def test_include_partially_eq_a_eq_b(self):
        self.v.include_partially(2, 7, 1)
        assert self.v.revealed == [slice(0, 3), slice(6, 10)]

    def test_include_partially_eq_a_gt_b(self):
        self.v.include_partially(2, 8, 1)
        assert self.v.revealed == [slice(0, 3), slice(6, 10)]

    def test_include_partially_in_ab_in_ab(self):
        self.v.include_partially(5, 6, 1)
        assert self.v.revealed == [slice(0, 2), slice(5, 6), slice(7, 10)]

    def test_include_partially_in_ab_eq_b(self):
        self.v.include_partially(5, 7, 1)
        assert self.v.revealed == [slice(0, 2), slice(5, 10)]

    def test_include_partially_in_ab_gt_b(self):
        self.v.include_partially(5, 8, 1)
        assert self.v.revealed == [slice(0, 2), slice(5, 10)]

    def test_include_partially_eq_b_gt_b(self):
        self.v.include_partially(7, 8, 1)
        assert self.v.revealed == [slice(0, 2), slice(7, 10)]

    def test_include_partially_gt_b_gt_b(self):
        self.v.include_partially(8, 9, 1)
        assert self.v.revealed == [slice(0, 2), slice(7, 10)]
