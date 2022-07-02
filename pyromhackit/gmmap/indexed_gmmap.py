from abc import ABCMeta, abstractmethod
from typing import Union

from pyromhackit.gmmap.gmmap import GMmap


class IndexedGMmap(GMmap, metaclass=ABCMeta):
    """ GMmap where the indices used to access elements in the sequence are either integers or slices. """

    def _logical2physical(self, location: Union[int, slice]):
        """ :return The location of the bytestring that encodes the element(s) at location @location of the sequence.
        :raise IndexError if @location is an integer and is out of bounds. """
        if isinstance(location, int):
            return self._logicalint2physical(location)
        elif isinstance(location, slice):
            return self._logicalslice2physical(location)
        else:
            raise TypeError("Unexpected location type: {}".format(type(location)))

    @abstractmethod
    def _logicalint2physical_unsafe(self, location: int):
        """ :return The slice for the bytestring that encodes the element(s) at integer index @location of the sequence.
        The behavior is undefined if @location is out of bounds. """
        raise NotImplementedError()

    def _logicalint2physical(self, location: int):  # Final
        """ :return The slice for the bytestring that encodes the element(s) at integer index @location of the sequence.
        :raise IndexError if @location is out of bounds. """
        if self._is_within_bounds(location):
            return self._logicalint2physical_unsafe(location)
        raise IndexError("Index out of bounds: {}".format(location))

    @abstractmethod
    def _is_within_bounds(self, location: int):
        """ :return True iff accessing this GMmap by index @location yields an element in the sequence. """
        raise NotImplementedError

    @abstractmethod
    def _logicalslice2physical(self, location: slice):
        """ :return The slice for the bytestring that encodes the element(s) at location @location of the sequence. """
        raise NotImplementedError()
