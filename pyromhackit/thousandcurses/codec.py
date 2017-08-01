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

from bidict import bidict

package_dir = os.path.dirname(os.path.abspath(__file__))


# The 'position' of a leaf is n iff it is the nth leaf of the tree.
# The 'position' of an internal node is the minimum 'position' of its descendant leaves.
class Tree(object):
    def __init__(self, arg, _position=0):
        #if not self.is_treelike(arg):
        #    raise ValueError("A tree is constructed from a non-empty nested sequence of trees, strings, or bytestrings."
        #                     " The presence of a string is mutually exclusive with the presence of a bytestring.")
        container_types = {tuple, list, Tree}
        self.type = None
        positions = []
        delta = _position
        self.children = []
        for c in arg:
            positions.append(delta)
            if any(isinstance(c, tpe) for tpe in container_types):
                infant = Tree(c, _position=delta)
                self.children.append(infant)
                delta += infant.numleaves
            else:
                self.children.append(c)
                delta += 1
        self.positions = tuple(positions)
        typeset = {c.type if isinstance(c, Tree) else type(c) for c in self.children}
        self.type = typeset.pop()
        self.numleaves = sum(1 if not isinstance(c, Tree) else c.numleaves for c in self.children)

    @classmethod
    def universal_type(cls, arg, leaf_predicate=lambda _: False):
        """ Returns the type common for all leaves in the tree-like (nested iterable) object, or None there is none. """

        def is_iterable(element):
            try:
                iter(element)
                return True
            except TypeError:
                return False

        if not is_iterable(arg) or leaf_predicate(arg):
            return type(arg)
        childtypes = [cls.universal_type(child, leaf_predicate) for child in arg]
        if any(t is None for t in childtypes) or len(set(childtypes)) > 1:
            return None
        return childtypes.pop()

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

    def flatten_without_joining(self):
        flat_list = []

        def append_or_recurse(element):
            if isinstance(element, Tree):
                for c in element:
                    append_or_recurse(c)
            else:
                flat_list.append(element)

        append_or_recurse(self)
        return Tree(flat_list)

    def list(self):
        return [c.list() if isinstance(c, Tree) else c for c in self.children]

    def reversed(self):
        return Tree(reversed(self))

    def inverted(self):
        return Tree([c.inverted() if isinstance(c, Tree) else c for c in self]).reversed()

    def offsets(self):
        t = tuple(c.numleaves if isinstance(c, Tree) else 1 for c in self)
        offsets = tuple(numpy.cumsum(t) - t)
        return offsets

    def map(self, fn):  # TODO Memory complexity
        """ Applies the given unary function to every leaf in this tree. """
        return Tree([c.map(fn) if isinstance(c, Tree) else fn(c) for c in self])

    def transliterate(self, codec: typing.Union[dict, bidict, 'Tree']) -> 'Tree':
        """ Replaces every leaf by its associated value in the dictionary @codec. Throws an exception if a key does not
        exist. If @codec is a pruning of a Tree of dictionaries T such that T shares the same structure as this Tree and
        such that every node in @codec has either no children or the same amount of children as the corresponding node
        in T, then every leaf below or at the node that corresponds to a dictionary will be replaced by the value that
        the dictionary associates the current leaf value to. If more than one dictionary has the same descendant leaf,
        the one closest to the descendant will take priority and the rest of the dictionaries will be ignored.
        """
        if isinstance(codec, dict) or isinstance(codec, bidict):
            return Tree(c.transliterate(codec) if isinstance(c, Tree) else codec[c] for c in self)
        lst = []
        for child, childcodec in zip(self, codec):
            if not isinstance(child, Tree):
                lst.append(childcodec[child])
            else:
                lst.append(child.transliterate(childcodec))
        return Tree(lst)

    def replace(self, replacements: dict) -> 'Tree':
        """ Returns the tree obtained by replacing leaves in this Tree by leaves in the dictionary @replacement. The
        dictionary maps the index path to a leaf in this Tree to the content it should be replaced with. """
        tree = self.list()
        for path in self.leaf_indices():
            current_children = tree
            for i in path[:-1]:
                current_children = current_children[i]
            current_children[path[-1]] = replacements[path]
        return Tree(tree)

    @classmethod
    def single_value_tree(cls, leafpaths, leafvalue=None):
        """ Returns a Tree having the structure given by @leafpaths, which is a set of index paths to leaves. Each leaf
        holds the (non-Tree) value @leafvalue. """
        assert not isinstance(leafvalue, Tree)
        children = []
        sortedleafpaths = sorted(leafpaths, key=lambda x: x[0])
        for path in sortedleafpaths:
            if len(children) <= path[0]:
                children += [leafvalue] * (path[0] - len(children) + 1)
            if len(path) == 1:  # Base case: The destination child is a leaf
                children[path[0]] = leafvalue
            else:  # Inductive case: The destination child is a subtree
                subtreeleafpaths = {p[1:] for p in leafpaths if p[0] == path[0]}
                children[path[0]] = cls.single_value_tree(subtreeleafpaths, leafvalue)
        return Tree(children)

    def restructured(self, leafpaths: typing.Union[dict, bidict]) -> 'Tree':
        """ Returns a Tree containing the same leaves as this Tree but has a structure defined by @leafpaths, which is
        a dictionary mapping the index path to a leaf in this Tree to an index path to the same leaf in the new
        Tree. """
        restructured = self.single_value_tree(leafpaths.values())
        leafpaths2content = {p2: self.reel_in(*p1) for p1, p2 in leafpaths.items()}
        return restructured.replace(leafpaths2content)


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

    def get_leaf_path(self, idx):
        return self.leaf_indices()[idx]

    def get_leaf(self, idx):
        return self.reel_in(*self.get_leaf_path(idx))

    def leaf_parent_indices(self):
        """ Returns a list of sequences of indices leading to a parent of a leaf, in a left-to-right
        depth-first-search manner. """
        leaf_paths = self.leaf_indices()
        parent_paths = [path[:-1] for path in leaf_paths]
        parent_paths = [p[0] for p in groupby(parent_paths)]
        return parent_paths

    def _position(self, *indexpath):
        """ Returns the position of the leaf given by the path of indices. """
        hook = self
        for i in indexpath[:-1]:
            hook = hook.children[i]
        return hook.positions[-1]

    def graph(self):
        grph = dict()
        leaf_indices = self.leaf_indices()
        for path in leaf_indices:
            position = self._position(*path)
            leaf_indices[position]
            originalpath = []
            subtree = self
            for nodeidx in path:
                orgnodepos = subtree.positions[nodeidx]
                originalpath.append(orgnodepos)
                subtree = subtree[nodeidx]
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
        if t1.graphically_equals(t2):
            return Tree._zip(t1, t2)
        else:
            raise ValueError("The structure of the trees differ.")

    @staticmethod
    def _zip(e1, e2):
        if isinstance(e1, Tree) and isinstance(e2, Tree):
            return Tree([Tree.zip(c1, c2) for c1, c2 in zip(e1, e2)])
        else:
            return e1, e2

    def traverse_preorder(self):
        """ Returns a generator for every node in the tree by doing a depth-first pre-order traversal. """

        def traverse(element):
            if isinstance(element, Tree):
                for child in element:
                    g = traverse(child)
                    for cc in g:
                        yield next(cc)
                    yield child
            else:
                yield element

        return traverse(self)

    def contentwise_equals(self, other: 'Tree'):
        """ True iff the (byte-)strings resulting from flattening the trees are equal. """
        return self.flatten() == other.flatten()

    def graphically_equals(self, other: 'Tree'):
        """ True iff the trees have the same set of vertices and same set of edges, disregarding all labels. """
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
        childrenstr = ",".join(str(c) if isinstance(c, Tree) else repr(c) for c in self.children)
        treestr = "({})".format(childrenstr)
        return treestr

    def __repr__(self):
        return self.__str__()


class MutableTree(object):
    """
    This is what a tree probably should be: a container for a nested list which can be mutated.
    After the user has defined a hierarchical ROM, he should create an instance of this class passing the ROM to the
    constructor, and apply any sequence of operations on the instance by calling its appropriate methods.
    """
    # TODO should this inherit Tree instead? would probably get easier to define operations

    def __init__(self, tree: Tree):
        self._tree = tree
        self.originalstate = dict()  # Calculate relation here. {(): (), (0,): (0,), (1,): (1,), ...}

    def transliterate(self, leafmap=dict()):
        """  """
        for leafparentpath in self._tree.leaf_parent_indices():
            pass

    def join(self, path=(), delim=''):
        """  """

    def zip(self):
        """  """

    def reverse(self, path=()):
        """ Reverse the children of the node that @path leads to. """
        self._tree.children.reverse()

    def invert(self):
        """ Reverse the children of all nodes. """
        for element in self._tree.traverse_preorder():
            if isinstance(element, Tree):
                element.reverse()


def identity_dict(n):
    """ n -> {(0,): {(0,)}, (1,): {(1,)}, ..., (n,): {(n,)}} """
    return dict([((a,), {(b,)}) for a, b in zip(range(n), range(n))])


def read_yaml(path):
    """ YAML -> Dictionary. """
    stream = open(path, 'r', encoding='utf8')
    dct = yaml.load(stream)
    return dct


def intersperse(bytestr, n):  # Not to be confused with e.g. Haskell's intersperse
    return [bytestr[i::n] for i in range(n)]


def treemap(fn, element):  # TODO Memory complexity
    if isinstance(element, Tree):
        tree = element
        return Tree([treemap(fn, c) for c in tree])
    return fn(element)


class Codec(ABC):
    @classmethod
    def operate(cls, tree: Tree):  # FIXME? Could take a MutableTree inheriting Tree as a parameter, including positions
        """ Performs any number of operations on the bytestring tree (mutates the object). Note that the original tree
        contains a 'position' attribute which the new tree and each of its nested subtrees will possess which is the
        position of the original (sub-)tree it corresponds to. By default performs no operation. """
        pass

    @classmethod
    @abstractmethod
    def decode(cls, bytetree: Tree) -> Tree:
        """ Decodes a bytestring tree into a string tree. The structure of the tree shall remain unchanged. """
        raise NotImplementedError("Decoder for {0} not implemented.".format(cls.__name__))

    @classmethod
    def decode_bytes(cls, bytestr: bytes) -> str:
        """ Decodes a bytestring into a string. There should be no reason to override this method. """
        btree = cls.domain(bytestr)
        cls.operate(btree)
        stree = cls.decode(btree)
        return stree.flatten()

    @classmethod
    @abstractmethod
    def encode(cls, s):
        raise NotImplementedError("Encoder for {0} not implemented.".format(cls.__name__))

    @classmethod
    def correspondence(cls, bytestr: bytes) -> (Tree, Tree, dict):
        """ Returns any triplet (B, S, F) which satisfies the following conditions:
        * B is a bytestring tree (nested list of bytestrings).
        * The flattening of B is equal to @bytestr.
        * S is a string tree (nested list of strings).
        * The flattening of S is equal to decode_bytes(@bytestr).
        * F is a dictionary mapping each leaf in any subset of B to a set of leaves in S. F is formally a dict mapping
          a tuple of integers to other tuples of integers so that each key tuple is a path of indices leading to a leaf
          in B and its associated value tuple is a path of indices leading to the corresponding leaf in S.
        * Each leaf L in B holds the property that, when modified, every leaf in S will remain unchanged except those
          in the set of leaves that F maps L to.
        * The algorithm is deterministic.
        That is, F is a "may affect only" relation from B to S. To include a pair (L1, L2) in F is to state that
        "The content of L2 is solely dependent on the content of L1".
        There should be no reason to override this method. Please override domain, operate and decode instead.
        """
        btree = cls.domain(bytestr)
        newbtree = Tree(btree)
        cls.operate(newbtree)
        stree = cls.decode(newbtree)
        graph = stree.graph()
        return btree, stree, graph


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


class ASCII(Codec):
    def decode(bytestr):
        return "".join(chr(b) for b in bytestr)

    def correspondence(bytestr):
        btree = Tree([bytes([b]) for b in bytestr]) if bytestr else Tree([b''])
        stree = treemap(ASCII.decode, btree)
        indexmap = identity_dict(len(btree.flatten()))
        return btree.list(), stree.list(), indexmap


class ReverseASCII(Codec):
    @classmethod
    def domain(cls, bytestr):
        return Tree([bytes([b]) for b in bytestr])

    @classmethod
    def operate(cls, tree):
        tree.invert()

    @classmethod
    def decode(cls, bytestuff):
        if isinstance(bytestuff, bytes):
            return "".join(reversed([chr(b) for b in bytestuff]))
        else:
            return Tree(bytestuff)


class MonospaceASCIIByte(Codec):
    """ Like ASCII, but replaces any unprintable and non-monospace character
    with some other (non-ascii) monospace character. """

    def decode(bytestr):
        b = bytestr[0]
        replacements = list(range(2 ** 8, 2 ** 9))
        if not chr(b).isprintable():
            return chr(replacements[b])
        return chr(b)


class MonospaceASCII(Codec):  # TODO Codec

    def decode(bytestr):
        return "".join(MonospaceASCIIByte.decode(bytes([b])) for b in bytestr)


class UppercaseASCII(Codec):
    def decode(bytestr):
        return "".join(MonospaceASCIIByte.decode(bytes([b]).upper()) for b in bytestr)

    def correspondence(bytestr):
        btree = Tree([bytes([b]) for b in bytestr]) if bytestr else Tree([b''])
        stree = treemap(UppercaseASCII.decode, btree)
        indexmap = identity_dict(len(btree.flatten()))
        return btree.list(), stree.list(), indexmap


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


ourcodecs = {c for (_, c) in
          inspect.getmembers(sys.modules[__name__],
                             lambda c: inspect.isclass(c) and issubclass(c, Codec) and c is not Codec)}
