from abc import ABCMeta, abstractmethod

from pyromhackit.gmmap.listlike_gmmap import ListlikeGMmap
from pyromhackit.gmmap.physically_indexed_gmmap import PhysicallyIndexedGMmap
from pyromhackit.gslice.selection import Selection


class SelectiveGMmap(ListlikeGMmap, PhysicallyIndexedGMmap, metaclass=ABCMeta):
    """ A ListlikeGMmap in which elements in the sequence can be marked/unmarked as being hidden from the user's
    purview. If the ith element is visible and becomes preceded by n hidden elements, that means that this element will
    henceforth be considered to be the (i-n)th element. """

    @property
    @abstractmethod
    def selection(self) -> Selection:
        raise NotImplementedError

    def _logicalint2physical(self, vindex: int):  # Final
        nonvindex = self.selection.virtual2physical(vindex)
        return self._nonvirtualint2physical(nonvindex)

    def _logicalslice2physical(self, vslice: slice):  # Final
        nonvselection = self.selection.virtual2physicalselection(vslice)
        return self._nonvirtualselection2physical(nonvselection)

    @abstractmethod
    def _nonvirtualint2physical(self, location: int) -> int:
        raise NotImplementedError

    @abstractmethod
    def _nonvirtualselection2physical(self, location: Selection) -> Selection:
        raise NotImplementedError

    def coverup(self, from_index, to_index):
        """ Let N denote the total number of elements in the sequence. This method causes every element with index i,
        where @from_index <= i < @to_index, to become hidden (if it is not already). """
        covered_count = self.selection.exclude(from_index, to_index)
        self._length -= covered_count

    def coverup_virtual(self, from_index, to_index):
        """ Let I_0, I_1, ..., I_(M-1) denote the indices of the visible elements in the sequence. This method causes
        every element with index I_i, where @from_index <= i < @to_index, to become hidden. """
        covered_count = self.selection.exclude_virtual(from_index, to_index)
        self._length -= covered_count

    def uncover(self, from_index, to_index):
        """ Let N denote the total number of elements in the sequence. This method causes every element with index i,
        where @from_index <= i < @to_index, to become visible (if it is not already). """
        revealed_count = self.selection.include(from_index, to_index)
        self._length += revealed_count

    def uncover_virtual(self, from_index, to_index):
        """ Let I_0, I_1, ..., I_(M-1) denote the indices of the visible elements in the sequence. This method causes
        every element with index i, where I_@from_index < i < I_@to_index, to become visible. If @from_index is None,
        and @to_index is not None, the condition becomes i < I_@to_index. If @from_index is not None and @to_index is
        None, the condition becomes I_@from_index < i. If both are None, all elements in the sequence become visible.
        """
        revealed_count = self.selection.include(from_index, to_index)
        self._length += revealed_count
