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


class Codec(ABC):
    @abstractmethod
    def encode(bytestr):
        pass

    @abstractmethod
    def decode(string):
        pass


class Hexify(Codec):
    def encode(string):
        raise NotImplementedError

    def decode(bytestr):
        return "".join(("0"+hex(n)[2:])[-2:].upper() for n in bytestr)


class HexifySpaces(Codec):
    def encode(string):
        raise NotImplementedError

    def decode(bytestr):
        return " ".join(Hexify.decode(bytes([n])) for n in bytestr)


class ASCII(Codec):
    def encode(string):
        raise NotImplementedError

    def decode(bytestr):
        return "".join(chr(b) for b in bytestr)


class MonospaceASCII(Codec):
    """ Like ASCII, but replaces any unprintable and non-monospace character
    with some other (non-ascii) monospace character. """
    def encode(string):
        raise NotImplementedError

    def decode(bytestr):
        b = bytestr[0]
        replacements = list(range(2**8, 2**9))
        if not chr(b).isprintable():
            return chr(replacements[b])
        return chr(b)


class MonospaceASCIISeq(Codec):
    def encode(string):
        raise NotImplementedError

    def decode(bytestr):
        return "".join(MonospaceASCII.decode(bytes([b])) for b in bytestr)


class MajinTenseiII(Codec):
    """ Bytestrings of length 1 """

    hexmap = os.path.join(package_dir, "resources/hexmap.yaml")
    transliter = read_yaml(hexmap)

    def encode(string):
        raise NotImplementedError

    def decode(bytestr):
        return MajinTenseiII.transliter[bytestr[0]]


class Mt2GarbageTextPair(Codec):
    def encode(string):
        raise NotImplementedError

    def decode(bytestr):
        garbage = "".join(MonospaceASCII.decode(bytes([b])) for b in
                          bytestr[1::2])
        text = "".join(MajinTenseiII.decode(bytes([b])) for b in bytestr[::2])
        return garbage+text
