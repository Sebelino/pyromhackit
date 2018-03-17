#!/usr/bin/env python

import os
from typing import Tuple, Optional, Union

import pytest

from pyromhackit.selection import Selection

package_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.mark.skip()  # TODO Do we need this? Skipping for now.
def test_err():
    with pytest.raises(AssertionError):
        Selection(slice(0, 0))


def test_simple():
    v = Selection(slice(0, 10))
    assert v.slices() == [slice(0, 10)]


def test_init2():
    v = Selection(slice(0, 10), revealed=[slice(3, 5)])
    assert v.slices() == [slice(3, 5)]


# TODO collect every test for a single MUT into a class
class TestInclude(object):
    @staticmethod
    @pytest.fixture(params=[
        ([(1, 9)], 9, 10, 1, [(1, 10)]),
        ([(1, 10)], None, None, 1, [(0, 10)]),
        ([(3, 7)], 1, 2, 1, [(1, 2), (3, 7)]),
        ([(3, 7)], 1, 3, 2, [(1, 7)]),
        ([(3, 7)], 1, 5, 2, [(1, 7)]),
        ([(3, 7)], 1, 7, 2, [(1, 7)]),
        ([(3, 7)], 1, 8, 3, [(1, 8)]),
        ([(3, 7)], 3, 3, 0, [(3, 7)]),
        ([(3, 7)], 3, 5, 0, [(3, 7)]),
        ([(3, 7)], 3, 7, 0, [(3, 7)]),
        ([(3, 7)], 3, 8, 1, [(3, 8)]),
        ([(3, 7)], 4, 6, 0, [(3, 7)]),
        ([(3, 7)], 4, 7, 0, [(3, 7)]),
        ([(3, 7)], 4, 8, 1, [(3, 8)]),
        ([(3, 7)], 7, 7, 0, [(3, 7)]),
        ([(3, 7)], 7, 8, 1, [(3, 8)]),
        ([(3, 7)], 8, 9, 1, [(3, 7), (8, 9)]),
        ([(3, 7)], 4, 10, 3, [(3, 10)]),
        ([(3, 7)], 4, 11, 3, [(3, 10)]),
        ([(3, 7)], 0, 0, 0, [(3, 7)]),
        ([(3, 7)], 10, 10, 0, [(3, 7)]),
        ([(4, 10)], 0, 10, 4, [(0, 10)]),
        ([(4, 10)], 2, 10, 2, [(2, 10)]),
        ([(2, 4), (6, 9)], 2, 5, 1, [(2, 5), (6, 9)]),
        ([(2, 4), (6, 9)], 4, 4, 0, [(2, 4), (6, 9)]),
        ([(2, 4), (6, 9)], 4, 5, 1, [(2, 5), (6, 9)]),
        ([(0, 2), (4, 6), (9, 10)], 1, 3, 1, [(0, 3), (4, 6), (9, 10)]),
        ([(0, 2), (4, 6), (9, 10)], 2, 3, 1, [(0, 3), (4, 6), (9, 10)]),
        ([(0, 2), (4, 6), (9, 10)], 2, 4, 2, [(0, 6), (9, 10)]),
        ([(0, 2), (4, 6), (9, 10)], 3, 7, 2, [(0, 2), (3, 7), (9, 10)]),
        ([(0, 2), (4, 6), (9, 10)], 8, 9, 1, [(0, 2), (4, 6), (8, 10)]),
        ([(0, 5)], 1, 2, 0, [(0, 5)]),
        ([(2, 5), (6, 9)], 9, 10, 1, [(2, 5), (6, 10)]),
    ])
    def data_and_expected(request):
        revealed, from_index, to_index, expected_return_value, expected_revealed = request.param
        object_under_test = Selection(universe=slice(0, 10), revealed=revealed)
        expected = Selection(universe=slice(0, 10), revealed=expected_revealed)
        return object_under_test, from_index, to_index, expected_return_value, expected

    @staticmethod
    @pytest.fixture()
    def data_and_expected_selection(data_and_expected):
        revealed, from_index, to_index, _, expected = data_and_expected
        return revealed, from_index, to_index, expected

    @staticmethod
    @pytest.fixture()
    def data_and_expected_return_value(data_and_expected):
        revealed, from_index, to_index, expected_return_value, _ = data_and_expected
        return revealed, from_index, to_index, expected_return_value

    @staticmethod
    def test_selection_matches_expected(data_and_expected_selection):
        object_under_test, from_index, to_index, expected = data_and_expected_selection
        object_under_test.include(from_index, to_index)
        assert list(object_under_test.pairs()) == list(expected.pairs())

    @staticmethod
    def test_selection_matches_return_value(data_and_expected_return_value):
        object_under_test, from_index, to_index, expected = data_and_expected_return_value
        returned = object_under_test.include(from_index, to_index)
        assert expected == returned

    @staticmethod
    def test_impl():  # Tests implementation details! Remove??
        s = Selection(universe=slice(0, 3), revealed=[])
        s.include(0, 3)
        assert list(s._intervals) == [3]


class TestExclude(object):
    @staticmethod
    @pytest.fixture(params=[
        ([], 0, 0, 0, []),
        ([], 0, 1, 0, []),
        ([], 0, 2, 0, []),
        ([], 0, 3, 0, []),
        ([], 0, None, 0, []),
        ([], 1, 0, 0, []),
        ([], 1, 1, 0, []),
        ([], 1, 2, 0, []),
        ([], 1, 3, 0, []),
        ([], 1, None, 0, []),
        ([], 2, 0, 0, []),
        ([], 2, 1, 0, []),
        ([], 2, 2, 0, []),
        ([], 2, 3, 0, []),
        ([], 2, None, 0, []),
        #([], 3, 0, 0, []),  # TODO these shouldn't raise AssertionError, since it's allowed for regular slices
        #([], 3, 1, 0, []),
        #([], 3, 2, 0, []),
        #([], 3, 3, 0, []),
        #([], 3, None, 0, []),
        ([], None, 0, 0, []),
        ([], None, 1, 0, []),
        ([], None, 2, 0, []),
        ([], None, 3, 0, []),
        ([], None, None, 0, []),
        ([(0, 1)], 0, 0, 0, [(0, 1)]),
        ([(0, 1)], 0, 1, 1, []),
        ([(0, 1)], 0, 2, 1, []),
        ([(0, 1)], 0, 3, 1, []),
        ([(0, 1)], 0, None, 1, []),
        ([(0, 1)], 1, 0, 0, [(0, 1)]),
        ([(0, 1)], 1, 1, 0, [(0, 1)]),
        ([(0, 1)], 1, 2, 0, [(0, 1)]),
        ([(0, 1)], 1, 3, 0, [(0, 1)]),
        ([(0, 1)], 1, None, 0, [(0, 1)]),
        ([(0, 1)], 2, 0, 0, [(0, 1)]),
        ([(0, 1)], 2, 1, 0, [(0, 1)]),
        ([(0, 1)], 2, 2, 0, [(0, 1)]),
        ([(0, 1)], 2, 3, 0, [(0, 1)]),
        ([(0, 1)], 2, None, 0, [(0, 1)]),
        #([(0, 1)], 3, 0, 0, [(0, 1)]),
        #([(0, 1)], 3, 1, 0, [(0, 1)]),
        #([(0, 1)], 3, 2, 0, [(0, 1)]),
        #([(0, 1)], 3, 3, 0, [(0, 1)]),
        #([(0, 1)], 3, None, 0, [(0, 1)]),
        ([(0, 1)], None, 0, 0, [(0, 1)]),
        ([(0, 1)], None, 1, 1, []),
        ([(0, 1)], None, 2, 1, []),
        ([(0, 1)], None, 3, 1, []),
        ([(0, 1)], None, None, 1, []),
        ([(0, 2)], 0, 0, 0, [(0, 2)]),
        ([(0, 2)], 0, 1, 1, [(1, 2)]),
        ([(0, 2)], 0, 2, 2, []),
        ([(0, 2)], 0, 3, 2, []),
        ([(0, 2)], 0, None, 2, []),
        ([(0, 2)], 1, 0, 0, [(0, 2)]),
        ([(0, 2)], 1, 1, 0, [(0, 2)]),
        ([(0, 2)], 1, 2, 1, [(0, 1)]),
        ([(0, 2)], 1, 3, 1, [(0, 1)]),
        ([(0, 2)], 1, None, 1, [(0, 1)]),
        ([(0, 2)], 2, 0, 0, [(0, 2)]),
        ([(0, 2)], 2, 1, 0, [(0, 2)]),
        ([(0, 2)], 2, 2, 0, [(0, 2)]),
        ([(0, 2)], 2, 3, 0, [(0, 2)]),
        ([(0, 2)], 2, None, 0, [(0, 2)]),
        #([(0, 2)], 3, 0, 0, [(0, 2)]),
        #([(0, 2)], 3, 1, 0, [(0, 2)]),
        #([(0, 2)], 3, 2, 0, [(0, 2)]),
        #([(0, 2)], 3, 3, 0, [(0, 2)]),
        #([(0, 2)], 3, None, 0, [(0, 2)]),
        ([(0, 2)], None, 0, 0, [(0, 2)]),
        ([(0, 2)], None, 1, 1, [(1, 2)]),
        ([(0, 2)], None, 2, 2, []),
        ([(0, 2)], None, 3, 2, []),
        ([(0, 2)], None, None, 2, []),
    ])
    def tiny_data_and_expected(request):
        revealed, from_index, to_index, expected_return_value, expected_revealed = request.param
        object_under_test = Selection(universe=slice(0, 2), revealed=revealed)
        expected = Selection(universe=slice(0, 2), revealed=expected_revealed)
        return object_under_test, from_index, to_index, expected_return_value, expected

    @staticmethod
    @pytest.fixture
    def tiny_data_and_expected_selection(tiny_data_and_expected):
        object_under_test, from_index, to_index, _, expected_revealed = tiny_data_and_expected
        return object_under_test, from_index, to_index, expected_revealed

    @staticmethod
    @pytest.fixture
    def tiny_data_and_expected_return_value(tiny_data_and_expected):
        object_under_test, from_index, to_index, expected_return_value, _ = tiny_data_and_expected
        return object_under_test, from_index, to_index, expected_return_value

    @staticmethod
    def test_tiny_selection_matches_expected(tiny_data_and_expected_selection):
        object_under_test, from_index, to_index, expected = tiny_data_and_expected_selection
        object_under_test.exclude(from_index, to_index)
        assert list(object_under_test.pairs()) == list(expected.pairs())

    @staticmethod
    def test_tiny_selection_matches_return_value(tiny_data_and_expected_return_value):
        object_under_test, from_index, to_index, expected = tiny_data_and_expected_return_value
        returned = object_under_test.exclude(from_index, to_index)
        assert expected == returned

    @staticmethod
    @pytest.fixture(params=[
        ([], 5, 10, 0, []),
        ([(0, 10)], 1, 2, 1, [(0, 1), (2, 10)]),
        ([(3, 7)], 0, 0, 0, [(3, 7)]),
        ([(3, 7)], 0, 7, 4, []),
        ([(3, 7)], 1, 2, 0, [(3, 7)]),
        ([(3, 7)], 1, 3, 0, [(3, 7)]),
        ([(3, 7)], 1, 5, 2, [(5, 7)]),
        ([(3, 7)], 1, 7, 4, []),
        ([(3, 7)], 1, 8, 4, []),
        ([(3, 7)], 3, 3, 0, [(3, 7)]),
        ([(3, 7)], 3, 5, 2, [(5, 7)]),
        ([(3, 7)], 3, 7, 4, []),
        ([(3, 7)], 3, 8, 4, []),
        ([(3, 7)], 4, 6, 2, [(3, 4), (6, 7)]),
        ([(3, 7)], 4, 7, 3, [(3, 4)]),
        ([(3, 7)], 4, 8, 3, [(3, 4)]),
        ([(3, 7)], 4, 10, 3, [(3, 4)]),
        ([(3, 7)], 4, 11, 3, [(3, 4)]),
        ([(3, 7)], 7, 7, 0, [(3, 7)]),
        ([(3, 7)], 7, 8, 0, [(3, 7)]),
        ([(3, 7)], 8, 9, 0, [(3, 7)]),
        ([(3, 7)], 10, 10, 0, [(3, 7)]),
        ([(0, 1), (2, 5)], 2, 3, 1, [(0, 1), (3, 5)]),
        ([(0, 1), (2, 5)], -8, 3, 1, [(0, 1), (3, 5)]),
        ([(0, 1), (2, 5)], 2, -7, 1, [(0, 1), (3, 5)]),
        ([(0, 3), (7, 10)], None, 1, 1, [(1, 3), (7, 10)]),
        ([(0, 3), (7, 10)], None, 7, 3, [(7, 10)]),
        ([(5, 6), (9, 10)], 10, None, 0, [(5, 6), (9, 10)]),
        ([(3, 4), (6, 9)], 4, 10, 3, [(3, 4)]),
        ([(0, 2), (4, 6), (9, 10)], 2, None, 3, [(0, 2)]),
        ([(0, 2), (5, 6), (9, 10)], None, 2, 2, [(5, 6), (9, 10)]),
        ([(0, 2), (5, 6), (9, 10)], None, 9, 3, [(9, 10)]),
        ([(0, 2), (3, 4), (5, 6), (8, 10)], 1, 9, 4, [(0, 1), (9, 10)]),
        ([(1, 2), (3, 4), (5, 6), (8, 10)], 1, 9, 4, [(9, 10)]),
    ])
    def data_and_expected(request):
        revealed, from_index, to_index, expected_return_value, expected_revealed = request.param
        object_under_test = Selection(universe=slice(0, 10), revealed=revealed)
        expected = Selection(universe=slice(0, 10), revealed=expected_revealed)
        return object_under_test, from_index, to_index, expected_return_value, expected

    @staticmethod
    @pytest.fixture
    def data_and_expected_selection(data_and_expected):
        object_under_test, from_index, to_index, _, expected_revealed = data_and_expected
        return object_under_test, from_index, to_index, expected_revealed

    @staticmethod
    @pytest.fixture
    def data_and_expected_return_value(data_and_expected):
        object_under_test, from_index, to_index, expected_return_value, _ = data_and_expected
        return object_under_test, from_index, to_index, expected_return_value

    @staticmethod
    def test_selection_matches_expected(data_and_expected_selection):
        object_under_test, from_index, to_index, expected_revealed = data_and_expected_selection
        object_under_test.exclude(from_index, to_index)
        assert list(expected_revealed.pairs()) == list(object_under_test.pairs())

    @staticmethod
    def test_selection_length(data_and_expected_selection):
        object_under_test, from_index, to_index, expected_revealed = data_and_expected_selection
        object_under_test.exclude(from_index, to_index)
        actual = len(object_under_test)
        expected = sum(b - a for a, b in expected_revealed.pairs())
        assert expected == actual

    @staticmethod
    def test_return_value_matches_expected(data_and_expected_return_value):
        object_under_test, from_index, to_index, expected = data_and_expected_return_value
        returned = object_under_test.exclude(from_index, to_index)
        assert returned == expected


class TestSubslice(object):
    @staticmethod
    @pytest.fixture(params=[
        ([(3, 4), (6, 9)], 6, 9, [(6, 9)]),
        ([(0, 2), (4, 6), (9, 10)], 0, 2, [(0, 2)]),
        ([(0, 2), (5, 6), (9, 10)], 2, 10, [(5, 6), (9, 10)]),
        ([(0, 2), (5, 6), (9, 10)], 9, 10, [(9, 10)]),
        ([(3, 4), (6, 9)], 2, 4, [(3, 4)]),
        ([(0, 2), (7, 10)], 0, 1, [(0, 1)]),
        ([(2, 7)], 1, 2, []),
        ([(2, 7)], None, 2, []),
        ([(2, 7)], 2, None, [(2, 7)]),
    ])
    def data(request):
        revealed, from_index, to_index, expected_revealed = request.param
        object_under_test = Selection(universe=slice(0, 10), revealed=revealed)
        expected = Selection(universe=slice(0, 10), revealed=expected_revealed)
        return object_under_test, from_index, to_index, expected

    @staticmethod
    def test_mut(data: Tuple[Selection, Optional[int], Optional[int], Selection]):
        object_under_test, from_index, to_index, expected = data
        returned = object_under_test.subslice(from_index, to_index)
        assert list(expected.pairs()) == list(returned.pairs())


class TestIncludePartiallyFromLeft(object):
    @staticmethod
    @pytest.fixture(params=[
        ([(2, 5), (6, 9)], 0, 10, 1, [(0, 1), (2, 5), (6, 9)]),
        ([(2, 5), (6, 9)], 2, 10, 1, [(2, 9)]),
        ([(2, 5), (6, 9)], 5, 10, 1, [(2, 9)]),
        ([(2, 5), (6, 9)], 9, 10, 1, [(2, 5), (6, 10)]),
        ([(0, 2), (4, 6), (9, 10)], 1, 9, 1, [(0, 3), (4, 6), (9, 10)]),
        ([(0, 2), (7, 10)], 1, 2, 1, [(0, 2), (7, 10)]),
    ])
    def data(request):
        revealed, from_index, to_index, count, expected_revealed = request.param
        object_under_test = Selection(universe=slice(0, 10), revealed=revealed)
        expected = Selection(universe=slice(0, 10), revealed=expected_revealed)
        return object_under_test, from_index, to_index, count, expected

    @staticmethod
    def test_mut(data: Tuple[Selection, Optional[int], Optional[int], int, Selection]):
        object_under_test, from_index, to_index, count, expected = data
        object_under_test._include_partially_from_left(from_index, to_index, count)
        assert list(object_under_test.pairs()) == list(expected.pairs())


class TestIncludePartiallyFromRight(object):
    @staticmethod
    @pytest.fixture(params=[
        ([(0, 2), (4, 6), (9, 10)], 1, 9, 1, [(0, 2), (4, 6), (8, 10)]),
        ([(0, 3), (4, 6), (9, 10)], 2, 4, 1, [(0, 6), (9, 10)]),
        ([(2, 4), (6, 9)], 0, 2, 1, [(1, 4), (6, 9)]),
    ])
    def data(request):
        revealed, from_index, to_index, count, expected_revealed = request.param
        object_under_test = Selection(universe=slice(0, 10), revealed=revealed)
        expected = Selection(universe=slice(0, 10), revealed=expected_revealed)
        return object_under_test, from_index, to_index, count, expected

    @staticmethod
    def test_mut(data: Tuple[Selection, Optional[int], Optional[int], int, Selection]):
        object_under_test, from_index, to_index, count, expected = data
        object_under_test._include_partially_from_right(from_index, to_index, count)
        assert list(object_under_test.pairs()) == list(expected.pairs())


class TestIncludePartially(object):
    @staticmethod
    @pytest.fixture(params=[
        ([(0, 2), (7, 10)], 0, 1, 1, [(0, 2), (7, 10)]),
        ([(0, 2), (7, 10)], 1, 2, 1, [(0, 2), (7, 10)]),
        ([(0, 2), (7, 10)], 1, 5, 1, [(0, 3), (4, 5), (7, 10)]),
        ([(0, 2), (7, 10)], 1, 7, 1, [(0, 3), (6, 10)]),
        ([(0, 2), (7, 10)], 1, 8, 1, [(0, 3), (6, 10)]),
        ([(0, 2), (7, 10)], 2, 5, 1, [(0, 3), (4, 5), (7, 10)]),
        ([(0, 2), (7, 10)], 2, 7, 1, [(0, 3), (6, 10)]),
        ([(0, 2), (7, 10)], 2, 8, 1, [(0, 3), (6, 10)]),
        ([(0, 2), (7, 10)], 5, 6, 1, [(0, 2), (5, 6), (7, 10)]),
        ([(0, 2), (7, 10)], 5, 7, 1, [(0, 2), (5, 10)]),
        ([(0, 2), (7, 10)], 5, 8, 1, [(0, 2), (5, 10)]),
        ([(0, 2), (7, 10)], 7, 8, 1, [(0, 2), (7, 10)]),
        ([(0, 2), (7, 10)], 8, 9, 1, [(0, 2), (7, 10)]),
        ([(0, 2), (4, 6), (9, 10)], None, None, 1, [(0, 3), (4, 6), (8, 10)]),
    ])
    def data(request):
        revealed, from_index, to_index, count, expected_revealed = request.param
        object_under_test = Selection(universe=slice(0, 10), revealed=revealed)
        expected = Selection(universe=slice(0, 10), revealed=expected_revealed)
        return object_under_test, from_index, to_index, count, expected

    @staticmethod
    def test_mut(data: Tuple[Selection, Optional[int], Optional[int], Union[int, Tuple[int, int]], Selection]):
        object_under_test, from_index, to_index, count, expected = data
        object_under_test.include_partially(from_index, to_index, count)
        assert list(object_under_test.pairs()) == list(expected.pairs())


class TestMultiplication(object):
    @staticmethod
    @pytest.fixture(params=[
        (Selection(slice(0, 10), []), 0, Selection(slice(0, 0), [])),
        (Selection(slice(0, 10), []), 1, Selection(slice(0, 10), [])),
        (Selection(slice(0, 10), []), 2, Selection(slice(0, 20), [])),
        (Selection(slice(0, 10), [(3, 5)]), 0, Selection(slice(0, 0), [])),
        (Selection(slice(0, 10), [(3, 5)]), 1, Selection(slice(0, 10), [(3, 5)])),
        (Selection(slice(0, 10), [(3, 5)]), 2, Selection(slice(0, 20), [(6, 10)])),
        (Selection(slice(0, 10), [(3, 5), (7, 10)]), 3, Selection(slice(0, 30), [(9, 15), (21, 30)])),
    ])
    def data_and_expected_return_value(request):
        factor1, factor2, expected_product = request.param
        return factor1, factor2, expected_product

    @staticmethod
    def test_mul(data_and_expected_return_value):
        factor1, factor2, expected_product = data_and_expected_return_value
        actual_product = factor1 * factor2
        assert expected_product == actual_product


class TestIter(object):
    @staticmethod
    def test_iter():
        sel = Selection(universe=slice(0, 10), revealed=[(4, 5), (7, 9)])
        assert [(a, b) for a, b in sel] == [(4, 5), (7, 9)]


class TestExcludeVirtual(object):
    @staticmethod
    @pytest.fixture(params=[
        ([(0, 5)], 1, 2, [(0, 1), (2, 5)]),
        ([(0, 1), (2, 5)], 1, 2, [(0, 1), (3, 5)]),
        ([(0, 5)], None, 7, []),
    ])
    def data(request):
        revealed, from_index, to_index, expected_revealed = request.param
        object_under_test = Selection(universe=slice(0, 10), revealed=revealed)
        expected = Selection(universe=slice(0, 10), revealed=expected_revealed)
        return object_under_test, from_index, to_index, expected

    @staticmethod
    def test_mut(data: Tuple[Selection, Optional[int], Optional[int], Selection]):
        object_under_test, from_index, to_index, expected = data
        object_under_test.exclude_virtual(from_index, to_index)
        assert list(object_under_test.pairs()) == list(expected.pairs())


class TestVirtualExclusion(object):
    def setup(self):
        self.v = Selection(slice(0, 5))

    def test_exclude_virtual_and_include_virtual(self):
        self.v.exclude_virtual(1, 2)
        self.v.exclude_virtual(1, 2)
        self.v.include_virtual(0, 1)
        assert self.v == Selection(universe=slice(0, 5), revealed=[slice(0, 5)])

    def test_exclude_virtual_all(self):
        self.v.exclude_virtual(None, 7)
        assert self.v == Selection(universe=slice(0, 5), revealed=[])


class TestGapSliceGap(object):
    def setup(self):
        self.v = Selection(universe=slice(0, 10), revealed=[slice(3, 7)])

    """ Misc """

    @pytest.mark.parametrize("pindex, expected", [
        (0, 0),
        (2, 0),
        (7, 1),
    ])
    @pytest.mark.skip()
    def test_gap_index(self, pindex, expected):
        assert self.v._gap_index(pindex) == expected


def test_exclude_all_and_include():
    v = Selection(slice(0, 10))
    v.exclude(0, 10)
    assert v.slices() == []
    v.include(3, 7)
    assert v.slices() == [slice(3, 7)]


class TestIndexing(object):
    def setup(self):
        self.v = Selection(slice(0, 10))
        self.v.exclude(0, 3)
        self.v.exclude(7, 10)

    @pytest.mark.skip()
    def test_index(self):
        assert self.v._index(5) == slice(3, 7)

    @pytest.mark.skip()
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
    assert selection.complement().slices() == expected


class TestThreeRevealedIntervals(object):
    def setup(self):
        self.v = Selection(universe=slice(0, 10), revealed=[slice(0, 2), slice(4, 6), slice(9, 10)])

    @pytest.mark.parametrize("pindex, expected", [
        (0, 0),
        (1, 0),
        (4, 1),
        (5, 1),
        (9, 2),
    ])
    @pytest.mark.skip()
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
    @pytest.mark.skip()
    def test_gap_index(self, pindex, expected):
        assert self.v._gap_index(pindex) == expected

    @pytest.mark.parametrize("from_index, to_index, expected_revealed", [
        (0, 10, [slice(0, 2), slice(4, 6), slice(9, 10)]),
        (None, None, [slice(0, 2), slice(4, 6), slice(9, 10)]),
    ])
    def test_subslice(self, from_index, to_index, expected_revealed):
        subsel = self.v.subslice(from_index, to_index)
        assert subsel.slices() == expected_revealed

    def test_complement_universe(self):
        assert self.v.complement().universe == self.v.universe

    def test_complement_revealed(self):
        assert self.v.complement().slices() == [slice(2, 4), slice(6, 9)]

    @pytest.mark.parametrize("from_index, to_index, count, expected_revealed", [
        (None, None, 1, [slice(0, 7), slice(8, 10)]),
        (None, None, (1, 1), [slice(0, 7), slice(8, 10)]),
        (None, None, (1, 0), [slice(0, 2), slice(3, 6), slice(8, 10)]),
        (None, None, (0, 1), [slice(0, 3), slice(4, 7), slice(9, 10)]),
        (None, None, 2, [slice(0, 10)]),
    ])
    def test_include_expand(self, from_index, to_index, count, expected_revealed):
        self.v.include_expand(from_index, to_index, count)
        assert self.v.slices() == expected_revealed


class TestThreeExcludedIntervals(object):
    def setup(self):
        self.v = Selection(universe=slice(0, 10), revealed=[slice(2, 4), slice(6, 9)])

    @pytest.mark.skip()
    @pytest.mark.parametrize("pindex, expected", [
        (0, 0),
        (1, 0),
        (4, 1),
        (5, 1),
        (9, 2),
    ])
    def test_gap_index(self, pindex, expected):
        assert self.v._gap_index(pindex) == expected

    @pytest.mark.parametrize("from_index, to_index, count, expected_revealed", [
        (None, None, 1, [slice(1, 10)]),
        (None, None, (1, 1), [slice(1, 10)]),
        (None, None, (1, 0), [slice(1, 4), slice(5, 9)]),
        (None, None, (0, 1), [slice(2, 5), slice(6, 10)]),
        (None, None, 2, [slice(0, 10)]),
    ])
    def test_include_expand(self, from_index, to_index, count, expected_revealed):
        self.v.include_expand(from_index, to_index, count)
        assert self.v.slices() == expected_revealed


class TestNormalization(object):
    def setup(self):
        self.v = Selection(slice(0, 5))

    def test_exclude_and_include(self):
        self.v.exclude(1, 2)
        self.v.include(2, 3)
        assert self.v.slices() == [slice(0, 1), slice(2, 5)]
