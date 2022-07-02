from pyromhackit.gmmap.bytestring_sourced_string_mmap import BytestringSourcedStringMmap
from pyromhackit.gmmap.selective_gmmap import SelectiveGMmap
from pyromhackit.gslice.selection import Selection


class SelectiveBytestringSourcedStringMmap(SelectiveGMmap, BytestringSourcedStringMmap):

    def __init__(self, bytestring_iterator, codec):
        super(SelectiveBytestringSourcedStringMmap, self).__init__(bytestring_iterator, codec)
        self._selection = Selection(universe=slice(0, self._length))

    @property
    def selection(self) -> Selection:
        return self._selection

    def _nonvirtualint2physical(self, location: int) -> slice:
        return slice(4 * location, 4 * (location + 1))

    def _nonvirtualselection2physical(self, location: Selection) -> Selection:
        return location * 4
