#!/usr/bin/env python

"""
Encoding/decoding functions.

An encoding function maps a bytestring to a unicode string.
A decoding function maps a unicode string to a bytestring.

Encoders/decoders are bijective -- each encoder has a inverse decoder function,
and vice versa.
"""

import os
import yaml
from abc import ABC, abstractmethod


package_dir = os.path.dirname(os.path.abspath(__file__))


def read_yaml(path):
    """ YAML -> Dictionary. """
    stream = open(path, 'r', encoding='utf8')
    dct = yaml.load(stream)
    return dct


def intersperse(bytestr, n):
    return [bytestr[i::n] for i in range(n)]


class Decoder(ABC):
    @classmethod
    @abstractmethod
    def decode(cls, bytestr):
        raise NotImplementedError("Decoder for {0} not implemented.".format(cls.__name__))


class Codec(Decoder):
    @classmethod
    @abstractmethod
    def encode(cls, s):
        raise NotImplementedError("Encoder for {0} not implemented.".format(cls.__name__))


class Hexify(Codec):
    def encode(s):
        return bytes([int(s[i:i+2], base=16) for i in range(0, len(s), 2)])

    def decode(bytestr):
        return "".join(("0"+hex(n)[2:])[-2:].upper() for n in bytestr)


class HexifySpaces(Codec):
    def encode(s):
        return bytes([int(b, base=16) for b in s.split()])

    def decode(bytestr):
        return " ".join(Hexify.decode(bytes([n])) for n in bytestr)


class ASCII(Codec):

    def decode(bytestr):
        return "".join(chr(b) for b in bytestr)


class MonospaceASCIIByte(Codec):
    """ Like ASCII, but replaces any unprintable and non-monospace character
    with some other (non-ascii) monospace character. """

    def decode(bytestr):
        b = bytestr[0]
        replacements = list(range(2**8, 2**9))
        if not chr(b).isprintable():
            return chr(replacements[b])
        return chr(b)


class MonospaceASCII(Codec):

    def decode(bytestr):
        return "".join(MonospaceASCIIByte.decode(bytes([b])) for b in bytestr)


class MajinTenseiII(Codec):
    hexmap = os.path.join(package_dir, "resources/hexmap.yaml")
    transliter = read_yaml(hexmap)

    def decode(bytestr):
        return "".join(MajinTenseiII.transliter[b] for b in bytestr)


class Mt2GarbageTextPair(Codec):

    def decode(bytestr):
        text, garbage = intersperse(bytestr, 2)
        result = MajinTenseiII.decode(text) + MonospaceASCII.decode(garbage)
        return result


names = {
    "Hexify": Hexify,
    "HexifySpaces": HexifySpaces,
    "ASCII": ASCII,
    "MonospaceASCIIByte": MonospaceASCIIByte,
    "MonospaceASCII": MonospaceASCII,
    "MajinTenseiII": MajinTenseiII,
    "Mt2GarbageTextPair": Mt2GarbageTextPair,
}
