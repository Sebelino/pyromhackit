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
import typing
from itertools import groupby
from queue import Queue

import numpy
import yaml
from abc import ABC, abstractmethod
import inspect
import treelib

package_dir = os.path.dirname(os.path.abspath(__file__))


class Tree(object):
    def __init__(self, arg, _position=0):
        if not self.is_treelike(arg):
            raise ValueError("A tree is constructed from a non-empty nested sequence of trees, strings, or bytestrings."
                             " The presence of a string is mutually exclusive with the presence of a bytestring.")
        self.tree = Tree()
        container_types = {tuple, list, Tree}
        self.type = None
        positions = []
        delta = 0
        self.children = []
        for c in arg:
            positions.append(delta)
            if any(isinstance(c, tpe) for tpe in container_types):
                infant = Tree(c, _position=_position + delta)
                self.children.append(infant)
                delta += infant.numleaves
            else:
                self.children.append(c)
                delta += 1
        self.positions = tuple(positions)
        typeset = {c.type if isinstance(c, Tree) else type(c) for c in self.children}
        self.type = typeset.pop()
        self.numleaves = sum(1 if not isinstance(c, Tree) else c.numleaves for c in self.children)

    @staticmethod
    def is_treelike(arg):
        """ True iff a tree can be constructed from the given object. """
        container_types = {tuple, list, Tree}
        content_types = {bytes, str}
        q = Queue()
        q.put(arg)
        content_type = None
        while not q.empty():
            element = q.get()
            for tpe in content_types:
                if isinstance(element, tpe):
                    if not content_type or isinstance(element, content_type):
                        content_type = tpe
                        break
                    elif not isinstance(element, content_type):
                        return False
            else:
                if not any(isinstance(element, tpe) for tpe in container_types):
                    return False
                if len(element) == 0:
                    return False
                for child in element:
                    q.put(child)
        return True

    def flatten(self):
        empty = self.type()
        return empty.join(c.flatten() if isinstance(c, Tree) else c for c in self.children)

    def list(self):
        return [c.list() if isinstance(c, Tree) else c for c in self.children]

    def invert(self):  # Mutability
        self.children.reverse()
        self.positions = tuple(reversed(self.positions))
        for c in self.children:
            if isinstance(c, Tree):
                c.invert()

    def offsets(self):
        t = tuple(c.numleaves if isinstance(c, Tree) else 1 for c in self)
        offsets = tuple(numpy.cumsum(t) - t)
        return offsets

    def map(self, fn):  # TODO Memory complexity
        """ Applies the given unary function to every leaf in this tree. """
        return Tree([c.map(fn) if isinstance(c, Tree) else fn(c) for c in self])

    def transliterate(self, dct):
        """ Replaces every leaf by its associated value in the argument dictionary. Throw an exception if a key
        does not exist. """
        return Tree([c.transliterate(dct) if isinstance(c, Tree) else dct[c] for c in self])

    def leaf_indices(self):
        """ Returns a list of sequences of indices leading to a leaf, in a left-to-right depth-first-search manner. """
        return self._leaf_indices([])

    def _leaf_indices(self, stack):
        paths = []
        for i in range(len(self.children)):
            if isinstance(self.children[i], Tree):
                for ci in self.children[i]._leaf_indices(stack + [i]):
                    paths.append(ci)
            else:
                paths.append(tuple(stack + [i]))
        return paths

    def leaf_parent_indices(self):
        """ Returns a list of sequences of indices leading to a parent of a leaf, in a left-to-right
        depth-first-search manner. """
        leaf_paths = self.leaf_indices()
        parent_paths = [path[:-1] for path in leaf_paths]
        parent_paths = [p[0] for p in groupby(parent_paths)]
        return parent_paths

    def graph(self):
        grph = dict()
        for path in self.leaf_indices():
            originalpath = []
            subtree = self
            for node in path:
                orgnode = subtree.positions[node]
                originalpath.append(orgnode)
                subtree = subtree[node]
            grph[tuple(originalpath)] = path
        return grph

    def reel_in(self, *args):
        hook = self
        for i in args:
            hook = hook.children[i]
        return hook

    def __getitem__(self, idx):
        if 0 <= idx < len(self.children):
            return self.children[idx]
        raise IndexError("Tree index out of range: {} in tree with {} elements".format(idx, len(self.children)))

    @staticmethod
    def zip(t1: 'Tree', t2: 'Tree'):
        """ Merges two trees with equal structure into one, where each leaf is a pair (A, B), where A is the
        corresponding leaf from the first tree and B is the corresponding leaf from the second. """
        if t1.structurally_equals(t2):
            return Tree._zip(t1, t2)
        else:
            raise ValueError("The structure of the trees differ.")

    @staticmethod
    def _zip(e1, e2):
        if isinstance(e1, Tree) and isinstance(e2, Tree):
            return Tree([Tree.zip(c1, c2) for c1, c2 in zip(e1, e2)])
        else:
            return e1, e2

    def contentwise_equals(self, other: 'Tree'):
        """ True iff the (byte-)strings resulting from flattening the trees are equal. """
        return self.flatten() == other.flatten()

    def graphically_equals(self, other: 'Tree'):
        """ True iff the trees have the same set of vertices and set of edges, disregarding all labels. """
        if len(other) != len(self):
            return False
        for a, b in zip(self, other):
            if isinstance(a, Tree) ^ isinstance(b, Tree):
                return False
            both_are_trees = isinstance(a, Tree)
            if both_are_trees and not a.graphically_equals(b):
                return False
        return True

    def deeply_equals(self, other: 'Tree'):
        """ True iff the trees are graphically equal and the content of the nth leaf of the first tree equals the
        content of the nth leaf of the second tree for every n. """
        if not self.graphically_equals(other):
            return False
        for a, b in zip(self, other):
            both_are_leaves = not isinstance(a, Tree)
            if both_are_leaves and a != b:
                return False
        return True

    def __eq__(self, other):
        """ True iff they are both Trees and all their fields contain equal data. """
        if not isinstance(other, Tree):
            return False
        if not self.deeply_equals(other):
            return False
        if self.positions != other.positions:
            return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __len__(self):
        return len(self.children)

    def __str__(self):
        childrenstr = ",".join(repr(c) for c in self.children)
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
    def domain(cls, bytestr):
        """ Returns any bytestring tree such that the flattening of it is equal to bytestr. By default returns a
        bytestring tree containing a single leaf. """
        return Tree([bytestr])

    @classmethod
    def operate(cls, tree):
        """ Performs any number of operations on the tree and returns the result. Note that the original tree
        contains a 'position' attribute which the new tree and each of its nested subtrees will possess
        which is the position of the original (sub-)tree it corresponds to. By default performs no operation. """
        return tree

    @classmethod
    @abstractmethod
    def decode(cls, bytestr) -> typing.Union[bytes, Tree]:
        """ Decodes a bytestring into a string, or a bytestring tree into a string tree. """
        raise NotImplementedError("Decoder for {0} not implemented.".format(cls.__name__))

    @classmethod
    def mapping(cls, bytestr: bytes) -> (Tree, Tree, dict):
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
