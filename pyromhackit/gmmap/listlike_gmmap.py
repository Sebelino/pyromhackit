import itertools
from abc import ABCMeta

from pyromhackit.gmmap.indexed_gmmap import IndexedGMmap


class ListlikeGMmap(IndexedGMmap, metaclass=ABCMeta):
    """ IndexedGMmap where
    * using an integer i as index yields the ith element in the sequence
    * using a slice(i, j) as index yields a the subsequence (a_i, a_(i+1), ..., a_j) where a is the sequence
    * negative integers are interpreted as counting from the end of the list.
    """

    def _is_within_bounds(self, location: int):
        """ :return True iff accessing this GMmap by index @location yields an element in the sequence. """
        return -len(self) <= location < len(self)

    def _recompute_length(self):
        """ :return The length of the sequence which is computed in O(n*log(n)) by finding the lowest non-negative index
        that raises an IndexError. """
        try:
            self._logicalint2physical(0)
        except IndexError:
            return 0
        # Find upper bound:
        for b in (2 ** i for i in itertools.count(1)):
            try:
                self._logicalint2physical(b)
            except IndexError:
                break
        a = 0
        while a < b:
            # INV: 0 = a < avg + 1 = length < b
            avg = a + (a + b) // 2
            try:
                self._logicalint2physical(avg)
                a = avg
            except IndexError:
                b = avg - 1
        return a + 1
