#!/usr/bin/env python

"""
Encoding/decoding functions.

An encoding function maps a bytestring to a unicode string.
A decoding function maps a unicode string to a bytestring.

Encoders/decoders are bijective -- each encoder has a inverse decoder function,
and vice versa.
"""

from abc import ABC, abstractmethod
import yaml


def read_yaml(path):
    """ YAML -> Dictionary. """
    # TODO duplicate in pyromhackit
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


class MajinTenseiII(Codec):
    """ Bytestrings of length 1 """

    transliter = read_yaml("hexmap.yaml")

    def encode(string):
        raise NotImplementedError

    def decode(bytestr):
        return MajinTenseiII.transliter[bytestr[0]]


class Mt2GarbageTextPair(Codec):
    def encode(string):
        raise NotImplementedError

    def decode(bytestr):
        garbage = "".join(MajinTenseiII.decode(bytes([b])) for b in
                          bytestr[1::2])
        text = "".join(MajinTenseiII.decode(bytes([b])) for b in bytestr[::2])
        return garbage+text
