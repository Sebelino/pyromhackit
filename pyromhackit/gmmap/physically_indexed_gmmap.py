import mmap
from abc import ABCMeta
from typing import Union

from pyromhackit.gmmap.gmmap import GMmap
from pyromhackit.gslice.selection import Selection


class PhysicallyIndexedGMmap(GMmap, metaclass=ABCMeta):
    """ GMmap where each physical location that a logical location translates into is either a slice or a Selection. """

    def _physical2bytes(self, physicallocation: Union[slice, Selection], content: mmap.mmap) -> bytes:
        """ :return The bytestring obtained when accessing the @content mmap using @physicallocation. """
        if isinstance(physicallocation, slice):
            return content[physicallocation]
        elif isinstance(physicallocation, Selection):
            return physicallocation.select(content)
        raise TypeError
