#!/usr/bin/env python

import os
from pyromhackit.rom import ROM
from pyromhackit.morphism import Morphism
import pyromhackit.thousandcurses.codec as codec
from pyromhackit.roms.persona1usa.hexmap import transliter

package_dir = os.path.dirname(os.path.abspath(__file__))

rom_path = os.path.join(package_dir, "resources/copyrighted/TENSI.BIN")


class Persona1Codec(codec.Decoder):
    @classmethod
    def domain(cls, bytestr: bytes):
        return codec.Tree([bytestr[i:i + 2] for i in range(0, len(bytestr), 2)])

    @classmethod
    def decode(cls, btree: codec.Tree):
        return btree.transliterate(transliter)


if __name__ == '__main__':
    r = ROM(rom_path)
    r2 = r[25704*2:25704*2+100]
    f2 = Morphism(r2, Persona1Codec)
    f = Morphism(r, Persona1Codec)

    print(f2)
