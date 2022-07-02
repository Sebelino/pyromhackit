from abc import ABCMeta

from pyromhackit.gmmap.additive import Additive
from pyromhackit.gmmap.listlike_gmmap import ListlikeGMmap
from pyromhackit.gmmap.physically_indexed_gmmap import PhysicallyIndexedGMmap


class BytesMmap(Additive, ListlikeGMmap, PhysicallyIndexedGMmap, metaclass=ABCMeta):
    """ A ListlikeGMmap where each element in the sequence is a bytestring of any positive length. """

    @classmethod
    def _decode(cls, bytestring: bytes):
        return bytestring

    @classmethod
    def _encode(cls, element) -> bytes:
        return element

    def __bytes__(self) -> bytes:  # Final
        """ :return The concatenation of all elements in the sequence. """
        return self[:]

    def iterbytes(self):
        """ :return A generator for every byte in every element in the sequence, left to right. """
        for bs in self:
            for b in bs:
                yield b

    def bytecount(self):
        """ :return The total number of bytes in this sequence. """
        return len(self._content)  # Assumes that self[:] == bytes(mmap)

    def __add__(self, operand: bytes) -> bytes:
        """ :return A bytestring being the concatenation of the sequence's bytestring representation and @operand. """
        return bytes(self) + operand

    def __radd__(self, operand: bytes) -> bytes:
        """ :return A bytestring being the concatenation of @operand and the sequence's bytestring representation. """
        return operand + bytes(self)
