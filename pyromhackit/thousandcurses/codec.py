#!/usr/bin/env python

"""
Encoding/decoding functions.

An encoding function maps a bytestring to a unicode string.
A decoding function maps a unicode string to a bytestring.

Encoders/decoders are bijective -- each encoder has a inverse decoder function,
and vice versa.
"""

import sys
import os

import numpy
import yaml
from abc import ABC, abstractmethod
import inspect
from queue import Queue

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
            self.numleaves = sum(1 if not isinstance(c, Tree) else c.numleaves for c in self.children)
        else:
            raise ValueError("A tree is constructed from a non-empty list/tuple of trees, strings, or bytestrings. "
                             "The presence of a string is mutually exclusive with the presence of a bytestring.")

    def flatten(self):
        empty = self.type()
        return empty.join(c.flatten() if isinstance(c, Tree) else c for c in self.children)

    def list(self):
        return [c.list() if isinstance(c, Tree) else c for c in self.children]

    def offsets(self):
        t = tuple(c.numleaves if isinstance(c, Tree) else 1 for c in self)
        offsets = tuple(numpy.cumsum(t)-t)
        return offsets

    def annotate(self):  # Mutability
        """ Adds an attribute, 'position', to this tree and all nested subtrees, so that the flattening of each tree
        is a substring of the flattening of the entire tree and the index of the first element in the substring relative
        to the complete string is equal to the tree's position attribute. """
        self._annotate(0)

    def _annotate(self, position):
        self.position = position
        offset = position
        for c in self:
            if isinstance(c, Tree):
                c._annotate(offset)
                offset += c.numleaves
            else:
                offset += len(c)

    def leaf_indices(self):
        """ Returns a queue of sequences of indices leading to a leaf, in a left-to-right
        depth-first-search manner. """
        return self._leaf_indices([])

    def _leaf_indices(self, stack):
        q = Queue()
        for i in range(len(self.children)):
            if isinstance(self.children[i], Tree):
                self.children[i]._leaf_indices(stack+[i])
            else:
                q.queue(tuple(stack+[i]))
        return q

    def graph(self):
        for path in self.leaf_indices():
            self.reel_in(*path)
        return {(self.position,): ()}

    def reel_in(self, *args):
        hook = self
        for i in args:
            hook = hook.children[i]
        return hook

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


def identity_dict(n):
    """ n -> {(0,): {(0,)}, (1,): {(1,)}, ..., (n,): {(n,)}} """
    return dict([((a,), {(b,)}) for a, b in zip(range(n), range(n))])


def read_yaml(path):
    """ YAML -> Dictionary. """
    stream = open(path, 'r', encoding='utf8')
    dct = yaml.load(stream)
    return dct


def intersperse(bytestr, n):
    return [bytestr[i::n] for i in range(n)]


def treemap(fn, element):  # TODO Memory complexity
    if isinstance(element, Tree):
        tree = element
        return Tree([treemap(fn, c) for c in tree])
    return fn(element)


class Decoder(ABC):
    @classmethod
    @abstractmethod
    def decode(cls, bytestr):
        """ Decodes a bytestring into a string, or a bytestring tree into a string tree. """
        raise NotImplementedError("Decoder for {0} not implemented.".format(cls.__name__))

    @classmethod
    def domain(cls, bytestr):
        """ Returns any bytestring tree such that the flattening of it is equal to bytestr. By default returns a
        bytestring tree containing a single leaf. """
        return Tree([bytestr])

    @classmethod
    def operate(cls, tree):
        """ Performs any number of operations on the tree and returns the result. Note that if the original tree
        contains a 'position' attribute, the new tree and all its nested subtrees will each possess this attribute
        which is the position of the original (sub-)tree it corresponds to. """
        return tree

    @classmethod
    def mapping(cls, bytestr):
        """ Returns any triplet (B, S, F) which satisfies the following conditions:
        * B is a bytestring tree (nested list of bytestrings).
        * The flattening of B is equal to bytestr.
        * S is a string tree (nested list of strings).
        * The flattening of S is equal to decode(bytestr).
        * F is a dictionary mapping each leaf in B to a set of leaves in S. F is formally a dict mapping a tuple of
          integers to other tuples of integers so that each key tuple is a path of indices leading to a leaf in B and
          its associated value tuple is a path of indices leading to the corresponding leaf in S.
        * Each leaf L in B holds the property that, when modified, every leaf in S will remain unchanged except those
          in the set of leaves that F maps L to.
        * The algorithm is deterministic.
        There should be no reason to override this method.
        """
        btree = cls.domain(bytestr)
        btree.annotate()
        newbtree = cls.operate(btree)
        stree = cls.decode(newbtree)
        graph = stree.graph()
        return btree, stree, graph


class Codec(Decoder):
    @classmethod
    @abstractmethod
    def encode(cls, s):
        raise NotImplementedError("Encoder for {0} not implemented.".format(cls.__name__))


class Hexify(Codec):
    def encode(s):
        return bytes([int(s[i:i + 2], base=16) for i in range(0, len(s), 2)])

    def decode(bytestr):
        return "".join(("0" + hex(n)[2:])[-2:].upper() for n in bytestr)


class HexifySpaces(Codec):
    def encode(s):
        return bytes([int(b, base=16) for b in s.split()])

    def decode(bytestr):
        return " ".join(Hexify.decode(bytes([n])) for n in bytestr)


class ASCII(Decoder):
    def decode(bytestr):
        return "".join(chr(b) for b in bytestr)

    def mapping(bytestr):
        btree = Tree([bytes([b]) for b in bytestr]) if bytestr else Tree([b''])
        stree = treemap(ASCII.decode, btree)
        indexmap = identity_dict(len(btree.flatten()))
        return btree.list(), stree.list(), indexmap


class ReverseASCII(Decoder):
    def decode(bytestr):
        return "".join(reversed([chr(b) for b in bytestr]))


class MonospaceASCIIByte(Decoder):
    """ Like ASCII, but replaces any unprintable and non-monospace character
    with some other (non-ascii) monospace character. """

    def decode(bytestr):
        b = bytestr[0]
        replacements = list(range(2 ** 8, 2 ** 9))
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
        btree = Tree([bytes([b]) for b in bytestr]) if bytestr else Tree([b''])
        stree = treemap(UppercaseASCII.decode, btree)
        indexmap = identity_dict(len(btree.flatten()))
        return btree.list(), stree.list(), indexmap


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


decoders = {c for (_, c) in
            inspect.getmembers(sys.modules[__name__],
                               lambda c: inspect.isclass(c) and issubclass(c, Decoder) and c not in {Decoder, Codec})}
codecs = {c for (_, c) in
          inspect.getmembers(sys.modules[__name__],
                             lambda c: inspect.isclass(c) and issubclass(c, Codec) and c is not Codec)}
