from abc import ABCMeta

from pyromhackit.gmmap.gmmap import GMmap


class SettableGMmap(GMmap, metaclass=ABCMeta):
    def __setitem__(self, location, val):  # Final
        """ Sets the @location'th element to @val, if @location is an integer; or sets the sub-sequence retrieved when
        slicing the sequence with @location to @val, if @location is a slice. """
        bytestringrepr = self._encode(val)
        bytestringlocation = self._logical2physical(location)
        self._content[bytestringlocation] = bytestringrepr
