from pyromhackit.gmmap.bytes_mmap import BytesMmap


class SingletonBytesMmap(BytesMmap):
    """ The most useless subclass. Sequence containing a single bytestring element. """

    def _logicalint2physical_unsafe(self, location: int) -> slice:
        if location == 0:
            return slice(None, None)

    def _logicalslice2physical(self, location: slice) -> slice:
        if (location.start is None or location.start <= 0) and (location.stop is None or location.stop >= 1):
            return location
        return slice(0, 0)  # Empty slice
