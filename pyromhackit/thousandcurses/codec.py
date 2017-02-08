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


class Tree(object):
    def __init__(self, arg):
        container_types = {tuple, list, Tree}
        if any(isinstance(arg, tpe) for tpe in container_types) and len(arg) >= 1:
            self.type = None
            children = list(arg)
            self.children = [Tree(c) if any(isinstance(c, tpe) for tpe in container_types) else c for c in children]
            typeset = {c.type if isinstance(c, Tree) else type(c) for c in self.children}
            self.type = typeset.pop()
            if typeset:
                t = typeset.pop()
                raise TypeError("Tree contains elements of both type {} and {}.".format(self.type, t))
        else:
            raise ValueError("A tree is constructed from a non-empty list/tuple of trees, strings, or bytestrings. "
                             "The presence of a string is mutually exclusive with the presence of a bytestring.")

    def flatten(self):
        empty = self.type()
        return empty.join(c.flatten() if isinstance(c, Tree) else c for c in self.children)

    def list(self):
        return [c.list() if isinstance(c, Tree) else c for c in self.children]

    def __getitem__(self, idx):
        err = IndexError("Tree index out of range.")
        if not self.children and idx == 0:
            return self.content
        elif self.children:
            return self.children[idx]
        raise err

    def __len__(self):
        return len(self.children)

    def __str__(self):
        if not self.children:
            return "{}".format(repr(self.content))
        childrenstr = ",".join(str(c) for c in self.children)
        treestr = "({})".format(childrenstr)
        return treestr

    def __repr__(self):
        return self.__str__()

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


class ASCII(Decoder):

    def decode(bytestr):
        return "".join(chr(b) for b in bytestr)


class MonospaceASCIIByte(Decoder):
    """ Like ASCII, but replaces any unprintable and non-monospace character
    with some other (non-ascii) monospace character. """

    def decode(bytestr):
        b = bytestr[0]
        replacements = list(range(2**8, 2**9))
        if not chr(b).isprintable():
            return chr(replacements[b])
        return chr(b)


class MonospaceASCII(Decoder):  # TODO Codec

    def decode(bytestr):
        return "".join(MonospaceASCIIByte.decode(bytes([b])) for b in bytestr)


class UppercaseASCII(Decoder):

    def decode(bytestr):
        return "".join(MonospaceASCIIByte.decode(bytes([b]).upper()) for b in bytestr)

    def mapping(bytestr):
        """ Returns a triplet (B, S, F) where:
        * B is a bytestring tree (nested list of bytestrings), such that the flattening of B is equal to bytestr,
        * S is a string tree (nested list of strings), such that the flattening of S is equal to decode(bytestr),
        * F is a nested dictionary mapping each leaf in B to a set of leaves in S by their indices. """
        return ([b'A', b'b', b'c'], ['A', 'B', 'C'], {0: {0}, 1: {1}, 2: {2}})


class MajinTenseiII(Decoder):
    hexmap = os.path.join(package_dir, "resources/hexmap.yaml")
    transliter = read_yaml(hexmap)

    def decode(bytestr):
        return "".join(MajinTenseiII.transliter[b] for b in bytestr)


class Mt2GarbageTextPair(Decoder):

    def decode(bytestr):
        text, garbage = intersperse(bytestr, 2)
        result = MajinTenseiII.decode(text) + MonospaceASCII.decode(garbage)
        return result


codecnames = {
    "Hexify": Hexify,
    "HexifySpaces": HexifySpaces,
}

decodernames = {
    **codecnames,
    "ASCII": ASCII,
    "MonospaceASCIIByte": MonospaceASCIIByte,
    "MonospaceASCII": MonospaceASCII,
    "MajinTenseiII": MajinTenseiII,
    "Mt2GarbageTextPair": Mt2GarbageTextPair,
}
