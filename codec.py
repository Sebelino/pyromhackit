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
    def encode(bytestr):
        raise NotImplementedError

    def decode(bytestr):
        return "".join(("0"+hex(n)[2:])[-2:].upper() for n in bytestr)


class MajinTenseiII(Codec):
    def encode(bytestr):
        raise NotImplementedError

    def decode(bytestr):
        transliteration = read_yaml("hexmap.yaml")
        garbage = "".join(transliteration[b] for b in bytestr[1::2])
        text = "".join(transliteration[b] for b in bytestr[::2])
        return garbage+text
