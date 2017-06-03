#!/usr/bin/env python


class Selection(object):
    def __init__(self, universe: slice, revealed=None):
        assert isinstance(universe, slice)
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
                    self.revealed[i:i+1] = [slice(a, from_index), slice(to_index, b)]
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
            yield (sl.start, sl.end)

    def __str__(self):
        return "{}(universe={}, revealed={})".format(self.__class__.__name__, self.universe, self.revealed)
