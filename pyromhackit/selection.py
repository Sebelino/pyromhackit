#!/usr/bin/env python
from abc import ABCMeta, abstractmethod
from copy import deepcopy


# TODO create interface/type Selection


class GSlice(metaclass=ABCMeta):  # TODO -> AbstractGSlice
    """ A GSlice (generalized slice) is any subset of the set of non-negative integers. It provides a way to select
     certain elements from a sequence. """

    @abstractmethod
    def select(self, sequence):
        """ :return A sequence x1, x2, ..., xn such that each xi is found in the sequence @sequence and the index of xi
        in @sequence increases monotonically w.r.t. i. The return value should not depend on the nature of the elements
        themselves. """
        raise NotImplementedError


class PrimitiveGSlice(GSlice, metaclass=ABCMeta):  # TODO rename
    pass


class Integer(PrimitiveGSlice):
    def __init__(self, *args):
        self.content = int(*args)

    def select(self, sequence):
        return sequence[self.content]

    def __call__(self, *args, **kwargs):
        return self.content


class Slice(PrimitiveGSlice):
    def __init__(self, *args):
        self.content = slice(*args)

    def select(self, sequence):
        return sequence[self.content]

    def __call__(self, *args, **kwargs):
        return self.content


class Selection(GSlice):  # TODO -> GSlice
    def __init__(self, universe: slice, revealed: list = None):
        assert isinstance(universe, slice)  # Should universe even be visible/exist?
        assert universe.start == 0
        assert isinstance(universe.stop, int)
        assert universe.stop >= 1
        self.universe = universe
        if revealed is None:
            self.revealed = [self.universe]
        else:
            self.revealed = revealed

    def coverup(self, from_index, to_index):
        """ Shrinks this selection by excluding any element with index i, where @from_index <= i < @to_index, if it is
            not already excluded.
            :return The number of revealed elements that were covered. """
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
            elif a < from_index < b:
                if to_index < b:
                    self.revealed[i:i + 1] = [slice(a, from_index), slice(to_index, b)]
                    i += 1
                elif b <= to_index:
                    self.revealed[i] = slice(a, from_index)
            elif b <= from_index:
                pass
            i += 1
        return original_length - len(self)

    def coverup_virtual(self, from_index, to_index):
        """ Shrinks this selection by excluding any element in the sub-sequence of visible elements with index i, where
            @from_index <= i < @to_index.
            :return The number of revealed elements that were covered. """
        if from_index is None or from_index < -len(self) or from_index >= len(self):
            p_from_index = None
        else:
            p_from_index = self.virtual2physical(from_index)
        if to_index is None or to_index < -len(self) or to_index >= len(self):
            p_to_index = None
        else:
            p_to_index = self.virtual2physical(to_index)
        return self.coverup(p_from_index, p_to_index)

    def reveal(self, from_index, to_index):
        """ Expands this selection by including any element with index i, where @from_index <= i < @to_index, if it is
            not already included.
            :return The number of covered elements that were revealed. """
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
            return to_index - from_index

        if self._within_bounds(from_index):
            m = self._slice_index(from_index)
            if self._within_bounds(to_index):
                n = self._slice_index(to_index)
                self.revealed[m:n + 1] = [slice(self.revealed[m].start, self.revealed[n].stop)]
            elif self._within_bounds(to_index + 1):
                n = self._slice_index(to_index + 1)
                self.revealed[m:n + 1] = [slice(self.revealed[m].start, self.revealed[n].stop)]
            else:
                n = self._gap_index(to_index)
                self.revealed[m:n] = [slice(self.revealed[m].start, to_index)]
        elif self._within_bounds(from_index - 1):
            m = self._slice_index(from_index - 1)
            if self._within_bounds(to_index):
                n = self._slice_index(to_index)
                self.revealed[m:n + 1] = [slice(self.revealed[m].start, self.revealed[n].stop)]
            elif self._within_bounds(to_index + 1):
                n = self._slice_index(to_index + 1)
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
        return len(self) - original_length

    def reveal_virtual(self, from_index, to_index):
        """ Expands this selection by including any element between the @from_index'th and @to_index'th visible
        elements. :return The number of revealed elements that were revealed. """
        if from_index is None or from_index < -len(self) or from_index >= len(self):
            p_from_index = None
        else:
            p_from_index = self.virtual2physical(from_index)
        if to_index is None or to_index < -len(self) or to_index >= len(self):
            p_to_index = None
        else:
            p_to_index = self.virtual2physical(to_index)
        return self.reveal(p_from_index, p_to_index)

    def __iter__(self):
        for sl in self.revealed:
            yield (sl.start, sl.stop)  # FIXME should probably generate slices instead, or every index

    def _slice_index(self, pindex):
        """ :return n if @pindex is in the nth slice (zero-indexed).
        :raise IndexError if @pindex is outside any slice. """
        for i, (a, b) in enumerate(self):
            if a <= pindex:
                if pindex < b:
                    return i
            else:
                break
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

    def index(self, pindex):
        """ Returns the slice that @pindex is in. """
        sliceindex = self._slice_index(pindex)
        return self.revealed[sliceindex]

    def select(self, listlike):
        """ Returns the selection of the subscriptable object @listlike. """
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

    def __len__(self):
        """ :return the total number of revealed elements. """
        return sum(segment.stop - segment.start for segment in self.revealed)

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
