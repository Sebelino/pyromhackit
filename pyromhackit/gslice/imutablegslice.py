from abc import ABCMeta, abstractmethod
from typing import Optional, Union, Tuple

from pyromhackit.gslice.igslice import IGSlice


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
