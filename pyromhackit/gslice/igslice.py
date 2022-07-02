from abc import ABCMeta, abstractmethod
from typing import Optional


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
