#!/usr/bin/env python
from abc import ABCMeta, abstractmethod
from copy import deepcopy

from typing import Optional, Union


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
        :return The number of excluded integers that were included. """
        raise NotImplementedError

    @abstractmethod
    def include_partially(self, from_index: Optional[int], to_index: Optional[int], count: Union[int, tuple]):
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
        :return The number of included elements that were excluded. """
        raise NotImplementedError

    def exclude_virtual(self, from_index: Optional[int], to_index: Optional[int]):
        """ Let S denote the sequence of integers currently included in this generalized slice. This method shrinks this
        generalized slice by excluding each ith integer in S, where @from_index <= i < @to_index.
        :return The number of included integers that were excluded. """
        raise NotImplementedError


class Selection(IMutableGSlice):
    def __init__(self, universe: slice, revealed: list = None):
        assert isinstance(universe, slice)  # Should universe even be visible/exist?
        assert universe.start == 0
        assert isinstance(universe.stop, int)
        assert universe.stop >= 1
        self.universe = universe
        if revealed is None:
            self.revealed = [self.universe]
        else:
            self.revealed = list(revealed)
        self._revealed_count = self._compute_len()

    def intervals(self):
        return self.revealed

    def exclude(self, from_index, to_index):
        original_length = len(self)
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
        i = 0
        while i < len(self.revealed):
            sl = self.revealed[i]
            a, b = sl.start, sl.stop
            if from_index <= a:
                if to_index <= a:
                    pass
                elif a < to_index < b:
                    self.revealed[i] = slice(to_index, b)
                elif b <= to_index:
                    self.revealed.pop(i)
                    i -= 1
            elif a < from_index < b:
                if to_index < b:
                    self.revealed[i:i + 1] = [slice(a, from_index), slice(to_index, b)]
                    i += 1
                elif b <= to_index:
                    self.revealed[i] = slice(a, from_index)
            elif b <= from_index:
                pass
            i += 1
        self._revealed_count = self._compute_len()
        return original_length - len(self)

    def exclude_virtual(self, from_index, to_index):
        if from_index is None or from_index < -len(self) or from_index >= len(self):
            p_from_index = None
        else:
            p_from_index = self.virtual2physical(from_index)
        if to_index is None or to_index < -len(self) or to_index >= len(self):
            p_to_index = None
        else:
            p_to_index = self.virtual2physical(to_index)
        return self.exclude(p_from_index, p_to_index)

    def include(self, from_index, to_index):
        original_length = len(self)
        if isinstance(from_index, int) and -self.universe.stop <= from_index < 0:
            from_index = from_index % self.universe.stop
        if isinstance(to_index, int) and -self.universe.stop <= to_index < 0:
            to_index = to_index % self.universe.stop
        assert from_index is None or self.universe.start <= from_index < self.universe.stop
        assert to_index is None or self.universe.start < to_index <= self.universe.stop
        if from_index is None:
            from_index = self.universe.start
        if to_index is None:
            to_index = self.universe.stop
        if not self.revealed:
            self.revealed.append(slice(from_index, to_index))
            self._revealed_count = self._compute_len()
            return to_index - from_index

        if self._within_bounds(from_index):
            m = self._slice_index(from_index)
            if self._within_bounds(to_index):
                n = self._slice_index(to_index)
                self.revealed[m:n + 1] = [slice(self.revealed[m].start, self.revealed[n].stop)]
            else:
                n = self._gap_index(to_index)
                self.revealed[m:n] = [slice(self.revealed[m].start, to_index)]
        elif self._within_bounds(from_index - 1):
            m = self._slice_index(from_index - 1)
            if self._within_bounds(to_index):
                n = self._slice_index(to_index)
                self.revealed[m:n + 1] = [slice(self.revealed[m].start, self.revealed[n].stop)]
            else:
                n = self._gap_index(to_index)
                self.revealed[m:n] = [slice(self.revealed[m].start, to_index)]
        else:
            m = self._gap_index(from_index)
            if self._within_bounds(to_index):
                n = self._slice_index(to_index)
                self.revealed[m:n + 1] = [slice(from_index, self.revealed[n].stop)]
            else:
                n = self._gap_index(to_index)
                self.revealed[m:n] = [slice(from_index, to_index)]
        self._revealed_count = self._compute_len()
        return len(self) - original_length

    def include_partially(self, from_index: Optional[int], to_index: Optional[int], count: Union[int, tuple]):
        if isinstance(count, int):
            return self.include_partially(from_index, to_index, (count, count))
        head_count, tail_count = count
        head_revealed_count = self._include_partially_from_left(from_index, to_index, head_count)
        tail_revealed_count = self._include_partially_from_right(from_index, to_index, tail_count)
        return head_revealed_count + tail_revealed_count

    def _include_partially_from_left(self, from_index: int, to_index: int, count: int):
        subsel = self.complement().subslice(from_index, to_index)
        revealed_count = 0
        for covered_start, covered_stop in subsel:
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
        subsel = self.complement().subslice(from_index, to_index)
        revealed_count = 0
        for covered_start, covered_stop in reversed(list(subsel)):
            coverage = covered_stop - covered_start
            if revealed_count + coverage < count:
                self.include(covered_start, covered_stop)
                revealed_count += coverage
            else:
                self.include(covered_stop - (count - revealed_count), covered_stop)
                revealed_count = count
                break
        return revealed_count

    def include_expand(self, from_index: Optional[int], to_index: Optional[int], count: Union[int, tuple]):
        if isinstance(count, int):
            return self.include_expand(from_index, to_index, (count, count))
        head_count, tail_count = count
        subsel = self.subslice(from_index, to_index)
        revealed_counter = 0
        for revealed_start, revealed_stop in subsel:
            try:
                previous_covered = self._previous_slice(slice(revealed_start, revealed_stop))
                revealed_counter += self._include_partially_from_right(previous_covered.start, revealed_start,
                                                                       head_count)
            except ValueError:
                pass
            try:
                next_covered = self._next_slice(slice(revealed_start, revealed_stop))
                revealed_counter += self._include_partially_from_left(revealed_stop, next_covered.stop, tail_count)
            except ValueError:
                pass
        return revealed_counter

    def _previous_slice(self, sl: slice):
        """ :return The revealed or covered slice immediately to the left of @sl.
        :raise ValueError if there is none. """
        if sl.start == self.universe.start:
            raise ValueError("There is no slice to the left of {}.".format(sl))
        # TODO O(n) -> O(1)
        zero_or_one = [s for s in self.revealed + self.complement().revealed if s.stop == sl.start]
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
        zero_or_one = [s for s in self.revealed + self.complement().revealed if s.start == sl.stop]
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
        for sl in self.revealed:
            yield (sl.start, sl.stop)  # FIXME should probably generate slices instead, or every index

    def complement(self):
        if len(self.revealed) == 0:
            return Selection(universe=self.universe, revealed=[self.universe])
        covered = []
        if self.revealed[0].start == self.universe.start:
            if self.revealed[-1].stop == self.universe.stop:
                previous_stop = self.revealed[0].stop
                for i in range(1, len(self.revealed)):
                    sl = self.revealed[i]
                    covered.append(slice(previous_stop, sl.start))
                    previous_stop = sl.stop
            else:
                previous_stop = self.revealed[0].stop
                for i in range(1, len(self.revealed)):
                    sl = self.revealed[i]
                    covered.append(slice(previous_stop, sl.start))
                    previous_stop = sl.stop
                covered.append(slice(self.revealed[-1].stop, self.universe.stop))
        else:
            if self.revealed[-1].stop == self.universe.stop:
                covered.append(slice(self.universe.start, self.revealed[0].start))
                previous_stop = self.revealed[0].stop
                for i in range(1, len(self.revealed)):
                    sl = self.revealed[i]
                    covered.append(slice(previous_stop, sl.start))
                    previous_stop = sl.stop
            else:
                covered.append(slice(self.universe.start, self.revealed[0].start))
                previous_stop = self.revealed[0].stop
                for i in range(1, len(self.revealed)):
                    sl = self.revealed[i]
                    covered.append(slice(previous_stop, sl.start))
                    previous_stop = sl.stop
                covered.append(slice(self.revealed[-1].stop, self.universe.stop))
        return Selection(universe=self.universe, revealed=covered)

    def subslice(self, from_index: Optional[int], to_index: Optional[int]):
        sel = Selection(universe=self.universe, revealed=list(self.revealed))
        if isinstance(from_index, int):
            sel.exclude(None, from_index)
        if isinstance(to_index, int):
            sel.exclude(to_index, None)
        return sel

    def _slice_index(self, pindex):
        """ :return n if @pindex is in the nth slice (zero-indexed).
        :raise IndexError if @pindex is outside any slice. """
        # Binary search
        lower = 0
        upper = len(self.revealed) - 1
        while lower <= upper:
            middle = (lower + upper) // 2
            midsl = self.revealed[middle]
            if pindex < midsl.start:
                upper = middle - 1
            elif midsl.stop <= pindex:
                lower = middle + 1
            else:  # midsl.start <= pindex < midsl.stop:
                return middle
        raise IndexError("{} is not in any interval.".format(pindex))

    def _gap_index(self, pindex):
        """ :return n if there are n slices to the left to @pindex.
        :raise IndexError if @pindex is in a slice. """
        n = 0
        for (a, b) in self:
            if a <= pindex:
                if pindex < b:
                    raise IndexError("{} is not in any gap.".format(pindex))
            else:
                break
            n += 1
        return n

    def _within_bounds(self, pindex):
        try:
            self._slice_index(pindex)
            return True
        except IndexError:
            return False

    def _index(self, pindex):
        """ Returns the slice that @pindex is in. """
        sliceindex = self._slice_index(pindex)
        return self.revealed[sliceindex]

    def select(self, listlike):
        # TODO only works for stringlike objects
        lst = []
        for interval in self.revealed:
            lst.append(listlike[interval])
        selection = listlike[0:0].join(lst)
        return selection

    def physical2virtual(self, pindex):
        vindex = 0
        for a, b in self:
            if a <= pindex < b:
                vindex += pindex - a
                return vindex
            vindex += b - a
        raise IndexError("Physical index {} out of bounds for selection {}".format(pindex, self))

    def virtual2physical(self, vindex):  # TODO -> virtualint2physical
        """ :return the integer n such that where the @vindex'th revealed element is the nth element. If
        @vindex < 0, @vindex is interpreted as (number of revealed elements) + @vindex.
        """
        if vindex < -len(self):
            raise IndexError(
                "Got index {}, expected it to be within range [{},{})".format(vindex, -len(self), len(self)))
        elif vindex < 0:
            return self.virtual2physical(len(self) + vindex)
        pindex = self.revealed[0].start
        cumlength = 0
        for a, b in self:
            cumlength += b - a
            if vindex < cumlength:
                pindex = b - (cumlength - vindex)
                if a <= pindex < b:
                    return pindex
                else:
                    break
        raise IndexError("Virtual index {} out of bounds for selection {}".format(vindex, self))

    def virtual2physicalselection(self, vslice: slice):  # TODO -> virtualslice2physical
        """ :return the sub-Selection that is the intersection of this selection and @vslice. """
        if not self.revealed or vslice.stop == 0:
            return Selection(self.universe, revealed=[])
        if vslice.start is None:
            a = self.revealed[0].start
        elif -len(self) <= vslice.start < len(self):
            a = self.virtual2physical(vslice.start)
        elif vslice.start >= len(self):
            a = self.revealed[-1].stop
        else:
            raise ValueError("Unexpected slice start: {}".format(vslice))
        if vslice.stop is None or vslice.stop >= len(self):
            b = self.revealed[-1].stop - 1
        elif -len(self) <= vslice.stop < len(self):
            b = self.virtual2physical(vslice.stop - 1)
        else:
            raise ValueError("Unexpected slice stop: {}".format(vslice))
        # INV: a is the physical index of the first element, b is the physical index of the last element
        if b < a:
            return Selection(universe=self.universe, revealed=[])
        m = self._slice_index(a)
        n = self._slice_index(b)
        intervals = self.revealed[m:n + 1]
        intervals[0] = slice(a, intervals[0].stop)
        intervals[-1] = slice(intervals[-1].start, b + 1)
        return Selection(universe=self.universe, revealed=intervals)

    def virtualselection2physical(self, vselection: 'Selection'):  # TODO -> virtualslice2physical
        """ :return the sub-Selection that is the intersection of this selection and @vselection. """
        intervals = []
        for start, stop in vselection:
            for a, b in self.virtual2physicalselection(slice(start, stop)):
                intervals.append(slice(a, b))
        return Selection(universe=self.universe, revealed=intervals)

    def __getitem__(self, item):
        return self.virtual2physical(item)

    def _compute_len(self):
        """ :return the total number of revealed elements. """
        return sum(segment.stop - segment.start for segment in self.revealed)

    def __len__(self):
        return self._revealed_count

    def __eq__(self, other):
        return repr(self) == repr(other)

    def __mul__(self, other: int):
        scaled_universe = slice(self.universe.start * other, self.universe.stop * other)
        scaled_revealed = [slice(s.start * other, s.stop * other) for s in self.revealed]
        return Selection(universe=scaled_universe, revealed=scaled_revealed)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __repr__(self):
        return "{}(universe={}, revealed={})".format(self.__class__.__name__, self.universe, self.revealed)

    def __str__(self):
        return repr(self)

    def __deepcopy__(self, memo):
        """ :return A deep copy of this object. """
        return Selection(universe=deepcopy(self.universe, memo), revealed=deepcopy(self.revealed, memo))
