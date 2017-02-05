#!/usr/bin/env python

import difflib
from .rom import ROM


class Morphism(object):
    """ A ROM paired with a string decoded from it using a specific decoder. The decoded string is a 'facet'
     of the ROM -- if the ROM is modified, the decoded string is generally modified as well. On the other hand,
     the decoded string cannot be directly modified, as it is solely dependent on the ROM and on the decoder.
     Formally, a Morphism is a function from the set of ROMs (bytestrings) to the set of strings.
     Unlike with an Isomorphism, multiple different ROMs can be decoded into the same string. You want to use this
     class if you have only implemented a decoder and/or if you are only interested in knowing how the decoded string
     changes as you edit the ROM. A typical use case scenario would be to to dump the in-game script for your ROM. """

    def __init__(self, rom_specifier, decoder):
        self.src = ROM(rom_specifier)
        self.decoder = decoder
        self.dst = decoder.decode(bytes(self.src))

    def source_diffusion(self, idx):
        """ Returns the indices of the bytes in the ROM affected
        when altering the ith character of the decoded string """
        self.src[idx]  # Raise IndexError?
        indices = set()
        for i in range(2 ** 8):
            alteration = self.src[:idx] + bytes([i]) + self.src[idx + 1:]
            dalteration = self.decoder.decode(alteration)
            diff = difflib.ndiff(dalteration, self.dst)
            adiff = [ds for ds in diff if ds[0] != '+']
            for j, s in enumerate(adiff):
                if s[0] == '-':
                    indices.add(j)
        return indices

    def impose_character(self, byteidx, stridx, c):
        """ By modifying the byteidx'th byte, find a byte value that causes the stridx'th character
        to become character c. Return None if no such value exists. """
        return None

    def impose_decoding(self, b, c):
        """ By modifying the way the decoder associates byte b to a character, find a decoder that associates
         b to character c. Return a new Morphism based on the altered decoder or None if no way to make such an
         alteration could be found. """
        newdecoder = self.decoder
        newdecoder[b] = c
        return Morphism(self.src, newdecoder)

    def dump(self, path):
        """ Dump the decoded string. """
        with open(path, 'w') as f:
            f.write(self.dst)

    def __str__(self):
        romstr = str(self.src).replace(self.src.__class__.__name__, self.__class__.__name__, 1)
        whitespace = " " * (len(self.__class__.__name__) + 2)
        dststr = repr(self.dst)
        result = "{},\n{}{})".format(romstr[:-1], whitespace, dststr)
        return result


class Isomorphism(Morphism):
    """ A ROM paired with a string decoded from it using a specific codec. The decoded string is simply another
    way to represent the ROM -- if the ROM is modified, so is the decoded string. Conversely, if the decoded string
    is modified, so is the ROM. Formally, an Isomorphism is a bijective function from the set of ROMs (bytestrings)
    to the set of strings. You want to use this class if you want to be able to edit the underlying ROM by editing a
    more user-friendly decoding of it. A typical use case scenario is to edit in-game text."""

    def impose_byte(self, stridx, byteidx, b):
        """ By modifying the stridx'th character, find a byte value that causes the stridx'th character
        to become character c. Return None if no such value exists. """
        return None
