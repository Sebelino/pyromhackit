#!/usr/bin/env python
from abc import ABCMeta, abstractmethod
from copy import deepcopy

from typing import Optional, Union, List, Tuple, Iterator

import itertools
from sortedcontainers import SortedSet


class IGSlice(metaclass=ABCMeta):
    """ A GSlice (generalized slice) is any subset of the set of non-negative integers, paired with an upper bound for
    them. It provides a way to select zero or more elements from a sequence. """

    @abstractmethod
    def select(self, sequence):
        """ :return A sequence x1, x2, ..., xn such that each xi is found in the sequence @sequence and the index of xi
        in @sequence increases monotonically w.r.t. i. The return value should not depend on the nature of the elements
        themselves. """
        raise NotImplementedError

    @abstractmethod
    def intervals(self):
        """ :return A sequence of pairs (a, b) such that for every a <= n < b, n is contained in this IGSlice. """
        raise NotImplementedError

    @abstractmethod
    def complement(self) -> 'IGSlice':
        """ :return An IGslice which is identical to this one except that for every 0 <= n < upperbound, n is contained
        in the IGSlice if and only if it was not contained in this one. """
        raise NotImplementedError

    def subslice(self, from_index: Optional[int], to_index: Optional[int]) -> 'IGSlice':
        """ :return A IGSlice which is identical to this one except that any integers outside
        [@from_index, @to_index) are excluded. """
        raise NotImplementedError

    def __len__(self):
        """ :return The cardinality of the set of integers. """
        raise NotImplementedError


class IMutableGSlice(IGSlice, metaclass=ABCMeta):
    """ An IMutableGSlice is an IGSlice where integers can be added or removed. """

    @abstractmethod
    def include(self, from_index: Optional[int], to_index: Optional[int]):
        """ Expands this generalized slice by including any integer in [@from_index, @to_index).
        :return The number of excluded integers that were included. Worst case O(n). """
        raise NotImplementedError

    @abstractmethod
    def include_partially(self, from_index: Optional[int], to_index: Optional[int], count: Union[int, Tuple[int, int]]):
        """ Let S be the sequence of excluded integers in [@from_index, @to_index). Includes the first n and the last m
        integers in S, where either n = m = @count or (n, m) = @count.
        :return The number of excluded elements that were included. """
        raise NotImplementedError

    @abstractmethod
    def include_virtual(self, from_index: Optional[int], to_index: Optional[int]):
        """ Let S denote the sequence of integers currently included in this generalized slice. This method expands this
        generalized slice by including each integer in [Sa, Sb), where Sa is the @from_index'th integer in S and Sb is
        the @to_index'th integer in S.
        :return The number of excluded integers that were included. """
        raise NotImplementedError

    @abstractmethod
    def include_partially_virtual(self, from_index: Optional[int], to_index: Optional[int], count: Union[int, tuple]):
        """ Let S denote the sequence of integers currently included in this generalized slice. This method expands this
        generalized slice by including the first n and the last m integers in [Sa, Sb), where Sa is the @from_index'th
        integer in S, Sb is the @to_index'th integer in S, and either n = m = @count or (n, m) = @count.
        :return The number of excluded integers that were included. """
        raise NotImplementedError

    @abstractmethod
    def include_expand(self, from_index: Optional[int], to_index: Optional[int], count: Union[int, tuple]):
        """ Let S be the subslice of this generalized slice where each integer is in [@from_index, @to_index). For each
        continuous sub-sequence of integers in S, includes every integer in [max(@from_index, a - n), a) and in
        [b, min(to_index, b + m)), where either n = m = @count or (n, m) = @count.
        :return The number of excluded elements that were included. """
        raise NotImplementedError

    @abstractmethod
    def exclude(self, from_index: Optional[int], to_index: Optional[int]):
        """ Shrinks this generalized slice by excluding any integer in [@from_index, @to_index).
        :return The number of included elements that were excluded.
        """
        raise NotImplementedError

    def exclude_virtual(self, from_index: Optional[int], to_index: Optional[int]):
        """ Let S denote the sequence of integers currently included in this generalized slice. This method shrinks this
        generalized slice by excluding each ith integer in S, where @from_index <= i < @to_index.
        :return The number of included integers that were excluded. """
        raise NotImplementedError


class Selection(IMutableGSlice):
    def __init__(
            self,
            universe: slice,
            revealed: list = None,
            intervals: Iterator = None,
            _length: Optional[int] = None  # For performance
    ):
        #assert isinstance(universe, slice)  # Should universe even be visible/exist?
        #assert universe.start == 0
        #assert isinstance(universe.stop, int)
        #assert universe.stop >= 1  # TODO Do we need this?
        self.universe = universe
        if intervals is None and revealed is None:
            self._intervals = self.revealed2sortedset([slice(0, universe.stop)])
        elif intervals is not None:
            self._intervals = SortedSet(intervals)
        else:
            self._intervals = self.revealed2sortedset(revealed)
        self._revealed_count = _length if isinstance(_length, int) else Selection._compute_len(self._intervals)

    @staticmethod
    def revealed2sortedset(revealed: List[Union[tuple, slice]]) -> SortedSet:
        """ Converts a list of included pairs to a sorted set of integers in O(n), n = size of @slices.
        Every number from every slice is added to the sorted set, except 0.
        """
        # 10, [] -> 10, []
        # 10, [(0, 10)] -> 10, [10]
        # 10, [(0, 7)] -> 10, [7]
        # 10, [(7, 10)] -> 10, [7, 10]
        # 10, [(3, 7)] -> 10, [3, 7]
        # 10, [(0, 3), (7, 10)] -> 10, [3, 7, 10]
        # 10, [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)] -> 10, [1, 2, 3, 4, 5, 6, 7, 8, 9]

        try:
            #intervals = SortedSet(a for a, _ in revealed).union(b for _, b in revealed)
            intervals = SortedSet()
            for a, b in revealed:
                intervals.add(a)
                intervals.add(b)
        except TypeError:  # slice
            intervals = SortedSet(sl.start for sl in revealed).union(sl.stop for sl in revealed)
        if 0 in intervals:
            intervals.remove(0)
        return intervals

    @staticmethod
    def sortedset2slices(sortedset: SortedSet) -> List[slice]:
        """ Converts a sorted set of integers to a list of included slices in O(n), n = size of @sortedset.
        If there is an even number of elements in @sortedset, the first slice is formed by the first and second
        numbers, the second slice is formed by the third and fourth numbers, and so on.
        If there is an odd number of elements in @sortedset, the pair consisting of the number 0 and the first element
        in @sortedset becomes the first slice in the output list. The remaining slices, if any, are formed by the
        second and third numbers, the fourth and fifth numbers, and so on.
        """
        slices = []
        if len(sortedset) % 2 == 0:
            for i in range(0, len(sortedset), 2):
                slices.append(slice(sortedset[i], sortedset[i + 1]))
        else:
            slices.append(slice(0, sortedset[0]))
            for i in range(1, len(sortedset), 2):
                slices.append(slice(sortedset[i], sortedset[i + 1]))
        return slices

    def slices(self) -> List[slice]:
        return self.sortedset2slices(self._intervals)

    def pairs(self) -> Iterator[Tuple[int, int]]:
        if len(self._intervals) % 2 == 0:
            return zip(self._intervals[::2], self._intervals[1::2])
        return itertools.chain([(0, self._intervals[0])], zip(self._intervals[1::2], self._intervals[2::2]))

    def gap_pairs(self) -> Iterator[Tuple[int, int]]:
        return self.complement().pairs()

    def intervals(self):
        return self._intervals

    def exclude(self, from_index: Optional[int], to_index: Optional[int]):
        original_length = self._revealed_count
        if isinstance(from_index, int) and -self.universe.stop <= from_index < 0:
            from_index = from_index % self.universe.stop
        if isinstance(to_index, int):
            if to_index > self.universe.stop:
                return self.exclude(from_index, None)
            if -self.universe.stop <= to_index < 0:
                to_index = to_index % self.universe.stop
        assert from_index is None or self.universe.start <= from_index <= self.universe.stop
        assert to_index is None or self.universe.start <= to_index <= self.universe.stop
        if from_index is None:
            from_index = self.universe.start
        if to_index is None:
            to_index = self.universe.stop
        if len(self._intervals) == 0:
            return 0
        if from_index >= to_index:
            return 0

        m = self._intervals.bisect_right(from_index)
        n = self._intervals.bisect_right(to_index)

        try:
            from_index_index = self._intervals.index(from_index)
        except ValueError:
            from_index_index = None
        try:
            to_index_index = self._intervals.index(to_index)
        except ValueError:
            to_index_index = None
        from_index_is_included = (
            len(self._intervals) % 2 == 0 and m % 2 == 1 or len(self._intervals) % 2 == 1 and m % 2 == 0)
        to_index_is_included = (
            len(self._intervals) % 2 == 0 and n % 2 == 1 or len(self._intervals) % 2 == 1 and n % 2 == 0)
        from_index_is_leftmost_included = from_index == 0 and from_index_is_included or from_index_index is not None and (
                len(self._intervals) % 2 == 0 and from_index_index % 2 == 0
                or len(self._intervals) % 2 == 1 and (from_index == 0 or from_index_index % 2 == 1))
        to_index_right_of_excluded = to_index_index is not None and (
                len(self._intervals) % 2 == 0 and to_index_index % 2 == 1
                or len(self._intervals) % 2 == 1 and (to_index == 0 or to_index_index % 2 == 0))

        if from_index_is_included:
            if from_index_is_leftmost_included:
                if to_index_is_included:
                    if m == 0:
                        to_remove = self._intervals[m:n]
                        endpoint = 0 if n == 0 else self._intervals[n - 1]
                        addendum = 0 if n == 0 else self._intervals[0]
                        self._revealed_count -= (to_index - endpoint) + addendum + sum(
                            b - a for a, b in zip(to_remove[1:-1:2], to_remove[2:-1:2]))
                        del self._intervals[m:n]
                        self._intervals.add(to_index)
                    else:
                        intermediates = self._intervals[m + 1:n - 1]
                        from_start, from_end = self._intervals[m - 1], self._intervals[m]
                        to_start, to_end = self._intervals[n - 1], self._intervals[n]
                        if m == n:
                            self._revealed_count -= to_index - from_start
                            self._intervals.remove(from_start)
                            self._intervals.add(to_index)
                        else:
                            self._revealed_count -= (from_end - from_start) + (to_index - self._intervals[n - 1]) + (
                                from_index - from_start) + sum(
                                b - a for a, b in zip(intermediates[::2], intermediates[1::2]))
                            del self._intervals[m + 1:n - 1]  # intermediates
                            self._intervals.remove(from_start)
                            self._intervals.remove(from_end)
                            self._intervals.remove(to_start)
                            self._intervals.add(to_index)
                else:
                    from_start = 0 if m == 0 else self._intervals[m - 1]
                    from_end = self._intervals[m]
                    self._revealed_count -= from_end - from_start
                    if from_start > 0:
                        self._intervals.remove(from_start)
                    self._intervals.remove(from_end)
            else:
                if to_index_is_included:
                    from_end = self._intervals[m]
                    to_start = self._intervals[n - 1]
                    if m == n:
                        self._revealed_count -= to_index - from_index
                        if from_index > 0:
                            self._intervals.add(from_index)
                        self._intervals.add(to_index)
                    else:
                        intermediates = self._intervals[m + 1:n - 1]
                        self._revealed_count -= (from_end - from_index) + (to_index - to_start) + sum(
                            b - a for a, b in zip(intermediates[::2], intermediates[1::2]))
                        del self._intervals[m + 1:n - 1]  # intermediates
                        if from_index > 0:
                            self._intervals.add(from_index)
                        self._intervals.add(to_index)
                        self._intervals.remove(from_end)
                        self._intervals.remove(to_start)
                else:
                    to_remove = self._intervals[m:n]
                    self._revealed_count -= self._intervals[m] - from_index + sum(b - a for a, b in zip(to_remove[1::2], to_remove[::2]))
                    del self._intervals[m:n]
                    if from_index != 0:
                        self._intervals.add(from_index)
        else:
            if to_index_is_included:
                if to_index_right_of_excluded:
                    to_remove = self._intervals[m:n - 1]
                    del self._intervals[m:n - 1]
                    self._revealed_count -= sum(b - a for a, b in zip(to_remove[::2], to_remove[1::2]))
                else:
                    to_remove = self._intervals[m:n]
                    del self._intervals[m:n]
                    self._intervals.add(to_index)
                    self._revealed_count -= (to_index - to_remove[0]) + sum(b - a for a, b in zip(to_remove[1::2], to_remove[::2]))
            else:
                to_remove = self._intervals[m:n]
                del self._intervals[m:n]
                self._revealed_count -= sum(b - a for a, b in zip(to_remove[::2], to_remove[1::2]))

        return original_length - self._revealed_count

    def exclude_virtual(self, from_index: Optional[int], to_index: Optional[int]):
        if from_index is None or from_index < -len(self) or from_index >= len(self):
            p_from_index = None
        else:
            p_from_index = self.virtual2physical(from_index)
        if to_index is None or to_index < -len(self) or to_index >= len(self):
            p_to_index = None
        else:
            p_to_index = self.virtual2physical(to_index)
        return self.exclude(p_from_index, p_to_index)

    def include(self, from_index: Optional[int], to_index: Optional[int]):
        original_length = len(self)
        if isinstance(from_index, int) and -self.universe.stop <= from_index < 0:
            from_index = from_index % self.universe.stop
        if isinstance(to_index, int):
            if to_index > self.universe.stop:
                return self.include(from_index, None)
            if -self.universe.stop <= to_index < 0:
                to_index = to_index % self.universe.stop
        assert from_index is None or self.universe.start <= from_index <= self.universe.stop
        assert to_index is None or self.universe.start <= to_index <= self.universe.stop
        if from_index is None:
            from_index = self.universe.start
        if to_index is None:
            to_index = self.universe.stop
        if not self._intervals:
            if from_index > 0:
                self._intervals.add(from_index)
            self._intervals.add(to_index)
            self._revealed_count += to_index - from_index
            return to_index - from_index
        if from_index == to_index:
            return 0

        m = self._intervals.bisect_right(from_index)
        n = self._intervals.bisect_right(to_index)

        try:
            from_index_index = self._intervals.index(from_index)
        except ValueError:
            from_index_index = None

        from_index_is_included = (
                len(self._intervals) % 2 == 0 and m % 2 == 1 or len(self._intervals) % 2 == 1 and m % 2 == 0)
        to_index_is_included = (
                len(self._intervals) % 2 == 0 and n % 2 == 1 or len(self._intervals) % 2 == 1 and n % 2 == 0)
        from_index_right_of_included = from_index_index is not None and (
                len(self._intervals) % 2 == 0 and from_index_index % 2 == 1
                or len(self._intervals) % 2 == 1 and from_index_index % 2 == 0)

        if from_index_is_included:
            if to_index_is_included:
                to_remove = self._intervals[m:n]
                del self._intervals[m:n]
                self._revealed_count += sum(b - a for a, b in zip(to_remove[::2], to_remove[1::2]))
            else:
                to_remove = self._intervals[m:n]
                del self._intervals[m:n]
                self._intervals.add(to_index)
                self._revealed_count += (to_index - to_remove[-1]) + sum(b - a for a, b in zip(to_remove[1::2], to_remove[::2]))
        else:
            if to_index_is_included:
                if from_index_right_of_included:
                    to_remove = self._intervals[m - 1:n]
                    del self._intervals[m - 1:n]
                    self._revealed_count += sum(b - a for a, b in zip(to_remove[::2], to_remove[1::2]))
                else:
                    to_remove = self._intervals[m:n]
                    del self._intervals[m:n]
                    self._intervals.add(from_index)
                    self._revealed_count += (to_remove[0] - from_index) + sum(b - a for a, b in zip(to_remove[1::2], to_remove[::2]))
            else:
                if from_index_right_of_included:
                    intermediates = self._intervals[m:n]
                    del self._intervals[m:n]  # intermediates
                    self._intervals.remove(from_index)
                    self._intervals.add(to_index)
                    self._revealed_count += (to_index - from_index) - sum(b - a for a, b in zip(intermediates[::2], intermediates[1::2]))
                else:
                    to_remove = self._intervals[m:n]
                    del self._intervals[m:n]
                    if from_index > 0:
                        self._intervals.add(from_index)
                    self._intervals.add(to_index)
                    self._revealed_count += (to_index - from_index) - sum(b - a for a, b in zip(to_remove[::2], to_remove[1::2]))

        return len(self) - original_length

    def include_partially(self, from_index: Optional[int], to_index: Optional[int], count: Union[int, tuple]):
        if isinstance(count, int):
            return self.include_partially(from_index, to_index, (count, count))
        head_count, tail_count = count
        head_revealed_count = self._include_partially_from_left(from_index, to_index, head_count)
        tail_revealed_count = self._include_partially_from_right(from_index, to_index, tail_count)
        return head_revealed_count + tail_revealed_count

    def _include_partially_from_left(self, from_index: int, to_index: int, count: int):
        if count == 0:
            return 0
        from_index, to_index = self._normalized_range(from_index, to_index)
        subsel = self._spanning_subslice(from_index, to_index).complement().subslice(from_index, to_index)

        revealed_count = 0
        for covered_start, covered_stop in subsel.pairs():
            coverage = covered_stop - covered_start
            if revealed_count + coverage < count:
                self.include(covered_start, covered_stop)
                revealed_count += coverage
            else:
                self.include(covered_start, covered_start + count - revealed_count)
                revealed_count = count
                break
        return revealed_count

    def _include_partially_from_right(self, from_index: int, to_index: int, count: int):
        if count == 0:
            return 0
        from_index, to_index = self._normalized_range(from_index, to_index)
        subsel = self._spanning_subslice(from_index, to_index).complement().subslice(from_index, to_index)

        revealed_count = 0
        for covered_start, covered_stop in reversed(list(subsel.pairs())):
            coverage = covered_stop - covered_start
            if revealed_count + coverage < count:
                self.include(covered_start, covered_stop)
                revealed_count += coverage
            else:
                self.include(covered_stop - (count - revealed_count), covered_stop)
                revealed_count = count
                break
        return revealed_count

    def include_expand(self, from_index: Optional[int], to_index: Optional[int], count: Union[int, Tuple[int, int]]):
        if isinstance(count, int):
            return self.include_expand(from_index, to_index, (count, count))
        if count == (0, 0):
            return 0
        head_count, tail_count = count
        revealed_counter = 0
        gaps = self.complement().subslice(from_index, to_index)
        for a, b in gaps.pairs():
            if b < self.universe.stop:
                revealed_counter += self._include_partially_from_right(a, b, head_count)
            if a > self.universe.start:
                revealed_counter += self._include_partially_from_left(a, b, tail_count)
        return revealed_counter

    def _previous_slice(self, sl: slice):
        """ :return The revealed or covered slice immediately to the left of @sl.
        :raise ValueError if there is none. """
        if sl.start == self.universe.start:
            raise ValueError("There is no slice to the left of {}.".format(sl))
        # TODO O(n) -> O(1)
        zero_or_one = [s for s in self._intervals + self.complement()._intervals if s.stop == sl.start]
        if len(zero_or_one) == 1:
            return zero_or_one[0]
        else:
            raise ValueError("Slice not found: {}.".format(sl))

    def _next_slice(self, sl: slice):
        """ :return The revealed or covered slice immediately to the right of @sl.
        :raise ValueError if there is none. """
        if sl.stop == self.universe.stop:
            raise ValueError("There is no slice to the right of {}.".format(sl))
        # TODO O(n)
        zero_or_one = [s for s in self._intervals + self.complement()._intervals if s.start == sl.stop]
        if len(zero_or_one) == 1:
            return zero_or_one[0]
        else:
            raise ValueError("Slice not found: {}.".format(sl))

    def include_virtual(self, from_index, to_index):
        if from_index is None or from_index < -len(self) or from_index >= len(self):
            p_from_index = None
        else:
            p_from_index = self.virtual2physical(from_index)
        if to_index is None or to_index < -len(self) or to_index >= len(self):
            p_to_index = None
        else:
            p_to_index = self.virtual2physical(to_index)
        return self.include(p_from_index, p_to_index)

    def include_partially_virtual(self, from_index: Optional[int], to_index: Optional[int], count: Union[int, tuple]):
        if from_index is None or from_index < -len(self) or from_index >= len(self):
            p_from_index = None
        else:
            p_from_index = self.virtual2physical(from_index)
        if to_index is None or to_index < -len(self) or to_index >= len(self):
            p_to_index = None
        else:
            p_to_index = self.virtual2physical(to_index)
        return self.include_partially(p_from_index, p_to_index, count)

    # FIXME Inconsistent with reversed(selection). Should probably make this use the default implementation and instead
    # rewrite this one to iter_slices or something.
    def __iter__(self):
        for a, b in self.pairs():
            yield a, b  # FIXME should probably generate slices instead, or every index

    def complement(self):
        if len(self._intervals) >= 1 and self._intervals[-1] == self.universe.stop:
            return Selection(universe=self.universe, intervals=self._intervals[:-1],
                             _length=self.universe.stop - len(self))
        return Selection(universe=self.universe, intervals=self._intervals.union([self.universe.stop]),
                         _length=self.universe.stop - len(self))

    def _normalized_range(self, from_index: Optional[int], to_index: Optional[int]) -> Tuple[int, int]:
        """ For any range [@from_index, @to_index) where the indices are either None or any integer, returns the
        equivalent range [x, y) such that either 0 <= x < y <= upper_bound or x = y = 0. The ranges are equivalent in
        the sense that when using them to slice this selection, they produce the same sub-selection. """
        if from_index is None or from_index <= -self.universe.stop:
            from_index = self.universe.start
        elif from_index > self.universe.stop:
            from_index = self.universe.stop
        elif -self.universe.stop <= from_index < 0:
            from_index = self.universe.stop - from_index

        if to_index is None or to_index >= self.universe.stop:
            to_index = self.universe.stop
        elif -self.universe.stop <= to_index < 0:
            to_index = self.universe.stop - to_index
        elif to_index < -self.universe.stop:
            to_index = self.universe.start

        if from_index >= to_index:
            from_index, to_index = (0, 0)
        return from_index, to_index

    def subslice(self, from_index: Optional[int], to_index: Optional[int]):
        from_index, to_index = self._normalized_range(from_index, to_index)
        sel = self._spanning_subslice(from_index, to_index)
        if len(sel._intervals) % 2 == 0:
            if len(sel) > 0:
                if sel._intervals[0] < from_index < sel._intervals[1]:
                    sel._revealed_count -= from_index - sel._intervals[0]
                    del sel._intervals[0]
                    sel._intervals.add(from_index)
                if sel._intervals[-2] < to_index < sel._intervals[-1]:
                    sel._revealed_count -= sel._intervals[-1] - to_index
                    del sel._intervals[-1]
                    sel._intervals.add(to_index)
        else:
            if 0 < from_index < sel._intervals[0]:
                sel._revealed_count -= from_index
                sel._intervals.add(from_index)
            if (len(sel._intervals) == 1 and to_index < sel._intervals[-1]
                    or len(sel._intervals) >= 2 and sel._intervals[-2] < to_index < sel._intervals[-1]):
                sel._revealed_count -= sel._intervals[-1] - to_index
                del sel._intervals[-1]
                sel._intervals.add(to_index)
        return sel

    def _spanning_subslice(self, from_index: int, to_index: int):
        """ :return A Selection whose set of revealed slices is a subset of that of this Selection such that every index
        in [from_index, to_index) is either on some slice in the subset, or on a gap. """
        if from_index >= to_index:
            return Selection(universe=deepcopy(self.universe), intervals=[])
        m = self._intervals.bisect_right(from_index)
        if len(self._intervals) % 2 == 0:
            n = self._intervals.bisect_left(to_index)
            intervals = self._intervals[m - (m % 2):n + (n % 2)]
        else:
            n = self._intervals.bisect_right(to_index)
            a = max(0, m - ((m + 1) % 2))
            b = n + ((n + 1) % 2)
            intervals = self._intervals[a:b]
        sel = Selection(universe=deepcopy(self.universe), intervals=intervals)
        return sel

    def _slow_subslice(self, from_index: Optional[int], to_index: Optional[int]):
        sel = self.deepcopy()
        if isinstance(from_index, int):
            sel.exclude(None, from_index)
        if isinstance(to_index, int):
            sel.exclude(to_index, None)
        return sel

    def _interval_index(self, pindex):
        """ :return n if the nth interval edge is the smallest number such that @pindex < n (zero-indexed). """
        lower = 0
        upper = len(self._intervals) - 1
        while lower <= upper:
            middle = (lower + upper) // 2
            midsl = self._intervals[middle]
            if pindex < midsl.start:
                upper = middle - 1
            elif midsl.stop <= pindex:
                lower = middle + 1
            else:  # midsl.start <= pindex < midsl.stop:
                return middle
        raise IndexError("{} is not in any interval.".format(pindex))

    def select(self, listlike):
        # TODO only works for stringlike objects
        lst = []
        for interval in self.slices():
            lst.append(listlike[interval])
        selection = listlike[0:0].join(lst)
        return selection

    def physical2virtual(self, pindex: int):
        vindex = 0
        for a, b in self.pairs():
            if a <= pindex < b:
                vindex += pindex - a
                return vindex
            vindex += b - a
        raise IndexError("Physical index {} out of bounds for selection {}".format(pindex, self))

    # TODO: O(n) -> O(log(n)) (using another sorted set for cumulative lengths?)
    def virtual2physical(self, vindex: int):  # TODO -> virtualint2physical
        """ :return the integer n such that where the @vindex'th revealed element is the nth element. If
        @vindex < 0, @vindex is interpreted as (number of revealed elements) + @vindex.
        """
        if vindex < -len(self):
            raise IndexError(
                "Got index {}, expected it to be within range [{},{})".format(vindex, -len(self), len(self)))
        elif vindex < 0:
            return self.virtual2physical(len(self) + vindex)
        cumlength = 0
        for a, b in self.pairs():
            cumlength += b - a
            if vindex < cumlength:
                pindex = b - (cumlength - vindex)
                if a <= pindex < b:
                    return pindex
                else:
                    break
        raise IndexError("Virtual index {} out of bounds for selection {}".format(vindex, self))

    def virtual2physicalselection(self, vslice: slice) -> 'Selection':  # TODO -> virtualslice2physical
        """ :return the sub-Selection that is the intersection of this selection and @vslice. """
        if not self._intervals or vslice.stop == 0:
            return Selection(self.universe, revealed=[])
        if vslice.start is None:
            a = self.virtual2physical(0)
        elif -len(self) <= vslice.start < len(self):
            a = self.virtual2physical(vslice.start)
        elif vslice.start >= len(self):
            a = self._intervals[-1]
        else:
            raise ValueError("Unexpected slice start: {}".format(vslice))
        if vslice.stop is None or vslice.stop >= len(self):
            b = self._intervals[-1] - 1
        elif -len(self) <= vslice.stop < len(self):
            b = self.virtual2physical(vslice.stop - 1)
        else:
            raise ValueError("Unexpected slice stop: {}".format(vslice))
        # INV: a is the physical index of the first element, b is the physical index of the last element
        if b < a:
            return Selection(universe=self.universe, revealed=[])
        m = self._intervals.bisect_right(a)
        n = self._intervals.bisect_right(b)
        intervals = SortedSet([a] + self._intervals[m:n] + [b + 1])
        return Selection(universe=self.universe, intervals=intervals)

    def virtualselection2physical(self, vselection: 'Selection'):  # TODO -> virtualslice2physical
        """ :return the sub-Selection that is the intersection of this selection and @vselection. """
        intervals = []
        for start, stop in vselection:
            for a, b in self.virtual2physicalselection(slice(start, stop)):
                intervals.append(slice(a, b))
        return Selection(universe=self.universe, revealed=intervals)

    def stretched(self, from_index: Optional[int], to_index: Optional[int]):  # TODO remove?
        """ :return A potentially shrinked deep copy of this selection, delimited by the universe
        [@from_index, @to_index). """
        m = self._intervals.bisect_right(from_index)
        n = self._intervals.bisect_right(to_index)
        intervals = self._intervals[m:n]
        return Selection(universe=slice(from_index, to_index), intervals=intervals)

    def __getitem__(self, item):
        return self.virtual2physical(item)

    @staticmethod
    def _compute_len(sortedset: SortedSet):
        """ :return The sum of the lengths of every slice in @slicelist. """
        if len(sortedset) == 0:
            return 0
        elif len(sortedset) % 2 == 0:
            return sum(sortedset[i + 1] - sortedset[i] for i in range(0, len(sortedset), 2))
        return sortedset[0] + sum(sortedset[i + 1] - sortedset[i] for i in range(1, len(sortedset), 2))

    def __len__(self):
        return self._revealed_count

    def __eq__(self, other):
        return repr(self) == repr(other)

    def __mul__(self, other: int):
        if other == 0:
            return Selection(universe=slice(0, 0), revealed=[])
        scaled_universe = slice(self.universe.start * other, self.universe.stop * other)
        scaled_revealed = [other * x for x in self._intervals]
        return Selection(universe=scaled_universe, intervals=scaled_revealed)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __repr__(self):
        return "{}(universe={}, intervals={})".format(self.__class__.__name__, self.universe, self._intervals)

    def __str__(self):
        return repr(self)

    def deepcopy(self):
        """ :return A deep copy of this object. """
        return Selection(universe=deepcopy(self.universe), intervals=deepcopy(self._intervals))
