from pyromhackit.gmmap.fixed_width_bytes_mmap import FixedWidthBytesMmap
from pyromhackit.gmmap.selective_gmmap import SelectiveGMmap
from pyromhackit.gslice.selection import Selection


class SelectiveFixedWidthBytesMmap(SelectiveGMmap, FixedWidthBytesMmap):
    def __init__(self, width, source):
        super(SelectiveFixedWidthBytesMmap, self).__init__(width, source)
        self._selection = Selection(universe=slice(0, self._length))

    @property
    def selection(self) -> Selection:
        return self._selection

    def _nonvirtualint2physical(self, location: int):
        return slice(self.width * location, self.width * (location + 1))

    def _nonvirtualselection2physical(self, location: Selection):
        return location * self.width
