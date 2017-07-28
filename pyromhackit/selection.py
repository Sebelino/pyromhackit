#!/usr/bin/env python
from abc import ABCMeta, abstractmethod


class GSlice(metaclass=ABCMeta):
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

    def reveal(self, from_index, to_index):
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
            return
        i = 0
        while i < len(self.revealed):
            sl = self.revealed[i]
            a, b = sl.start, sl.stop
            if from_index < a:
                if to_index < a:
                    self.revealed.insert(i, slice(from_index, to_index))
                    i += 1
                elif a <= to_index <= b:
                    self.revealed[i] = slice(from_index, b)
                elif b <= to_index:
                    self.revealed[i] = slice(from_index, to_index)
            elif a <= from_index <= b:
                if to_index <= b:
                    pass
                elif to_index > b:
                    self.revealed[i] = slice(a, to_index)
            elif b < from_index:
                self.revealed.insert(i + 1, slice(from_index, to_index))
                i += 1
            i += 1

    def __iter__(self):
        for sl in self.revealed:
            yield (sl.start, sl.stop)

    def _slice_index(self, pindex):
        """ Returns n if @pindex is in the nth slice. """
        i = 0
        for a, b in self:
            if a <= pindex:
                if pindex < b:
                    return i
                else:
                    break
            i += 1
        raise ValueError("{} is not in any interval.".format(pindex))

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

    def virtual2physical(self, vindex):
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

    def virtual2physicalselection(self, vslice: slice):
        """ Returns the sub-Selection that is the intersection of this selection and @vslice. """
        if not self.revealed:
            return Selection(self.universe, revealed=[])
        if vslice.start is None:
            a = self.revealed[0].start
        elif 0 <= vslice.start < len(self):
            a = self.virtual2physical(vslice.start)
        elif vslice.start >= len(self):
            a = self.revealed[-1].stop
        else:
            raise ValueError("Unexpected slice start: {}".format(vslice))
        if vslice.stop is None or vslice.stop >= len(self):
            b = self.revealed[-1].stop
        elif 0 <= vslice.stop < len(self):
            b = self.virtual2physical(vslice.stop)
        else:
            raise ValueError("Unexpected slice stop: {}".format(vslice))
        # INV: a is the physical index of the first element, b-1 is the physical index of the last element
        if b <= a:
            return Selection(universe=self.universe, revealed=[])
        m = self._slice_index(a)
        n = self._slice_index(b - 1)
        intervals = self.revealed[m:n + 1]
        intervals[0] = slice(a, intervals[0].stop)
        intervals[-1] = slice(intervals[-1].start, b)
        return Selection(universe=self.universe, revealed=intervals)

    def virtualselection2physical(self, vselection: 'Selection'):  # TODO -> virtualslice2physical
        """ :return the sub-Selection that is the intersection of this selection and @vselection. """
        intervals = []
        for start, stop in vselection:
            intervals.append(self.virtual2physicalselection(slice(start, stop)))
        return Selection(universe=self.universe, revealed=intervals)

    def __getitem__(self, item):
        return self.virtual2physical(item)

    def __len__(self):
        """ Returns the total number of revealed elements. """
        return sum(segment.stop - segment.start for segment in self.revealed)

    def __eq__(self, other):
        return repr(self) == repr(other)

    def __repr__(self):
        return "{}(universe={}, revealed={})".format(self.__class__.__name__, self.universe, self.revealed)

    def __str__(self):
        return repr(self)
