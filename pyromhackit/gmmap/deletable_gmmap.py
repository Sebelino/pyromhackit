from abc import ABCMeta, abstractmethod

from pyromhackit.gmmap.gmmap import GMmap


class DeletableGMmap(GMmap, metaclass=ABCMeta):
    @abstractmethod  # Can this be non-abstract? Hmm...
    def __delitem__(self, location):  # Final
        """ Removes the @location'th element, if @location is an integer; or the sub-sequence retrieved when slicing the
        sequence with @location, if @location is a slice. """
        raise NotImplementedError()
