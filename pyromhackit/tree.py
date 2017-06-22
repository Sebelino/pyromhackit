#!/usr/bin/env python
import os
from abc import abstractmethod
from collections import namedtuple

package_dir = os.path.dirname(os.path.abspath(__file__))


class Topology(object):
    """ A way of transforming a stringlike object into a list of stringlike objects, taking in account only the length
    of the object. """

    @abstractmethod
    def index2leafindex(self, idx):
        """ :return An index n such that the nth leaf contains the byte/character with index @idx in any stringlike
        object structured according to this Topology. """
        raise NotImplementedError()

    @abstractmethod
    def leafindex2indexpath(self, leafindex):
        """ :return An index path p leading to the @leafindex'th leaf for this Topology. """
        raise NotImplementedError()

    @abstractmethod
    def indexpath2index(self, indexpath):
        """ :return An index n such that the leaf that the path @indexpath leads to contains the nth byte/character
        in the stringlike object structured according to this Topology. """
        raise NotImplementedError()

    @abstractmethod
    def structure(self, stringlike):  # TODO can and should be implemented using leafindex2indexpath (?)
        """ Returns a nested list such that its flattening equals @stringlike, structured according to this Topology. """
        raise NotImplementedError()

    def traverse_preorder(self, stringlike):
        """ Returns a generator for a tuple (i, n, p, s) consisting of data for a leaf, where
        i is the byte/character index of the leaf
        n is the leaf index of the leaf
        p is the index path leading to the leaf
        s is the leaf's content
        """
        Leaf = namedtuple("Leaf", "index leafindex indexpath content")
        if not stringlike:
            return iter([])
        for leafidx in range(self.length(len(stringlike))):
            idxpath = self.leafindex2indexpath(leafidx)
            idx = self.indexpath2index(idxpath)
            yield (idx, leafidx, idxpath, self.getleaf(leafidx, stringlike))

    def length(self, size):
        """ :return the number of leaves in a tree for a stringlike object of size @size structured according to this
        Topology. """
        return self.index2leafindex(size - 1) + 1

    def getleaf(self, leafindex: int, stringlike):
        """ :return The @leafindex'th leaf in the stringlike object @stringlike. """
        a = self.indexpath2index(self.leafindex2indexpath(leafindex))
        b = self.indexpath2index(self.leafindex2indexpath(leafindex + 1))
        return stringlike[a:b]

    def __call__(self, *args, **kwargs):
        return self.structure(*args)

    def __str__(self):
        return self.__class__.__name__


class SingletonTopology(Topology):
    def structure(self, stringlike):
        return [stringlike]

    def index2leafindex(self, idx):
        return 0

    def leafindex2indexpath(self, leafindex):
        return 0,

    def indexpath2index(self, indexpath):
        return 0


class SimpleTopology(Topology):
    def __init__(self, *sizes):
        """ Encompasses the set of trees that consist of any number of children where each child is either a
        sub(-byte-)string or a subtree with a set structure common for all children. All leaves share the same length.
        @stringrepr is the string representation of a certain Tree structure. @stringrepr is a '-' separated string
        where each token is a positive integer. If the last token is n, each leaf in any Tree belonging to this Topology
        will be a string of length n. If the ith token is n, each subtree at the (i-1)th level of the tree will have
        n children (level zero being the root). """

        for s in sizes:
            assert isinstance(s, int)
        self.sizes = sizes

    def maketree(self, iterable):
        if len(self.sizes) == 1:
            return iterable
        elif len(self.sizes) == 2:
            lst = list(iterable)
            s = self.sizes[1]
            return list(zip(list(lst[i::s]) for i in range(s)))
        raise NotImplementedError()

    def structure(self, stringlike):
        # TODO generalize (recursion?)
        if len(self.sizes) == 1:
            n = self.sizes[0]
            return [stringlike[i:i + n] for i in range(0, len(stringlike), n)]
        elif len(self.sizes) == 2:
            sublistcount = int(len(stringlike) / self.sizes[0] / self.sizes[1])
            stringcount = self.sizes[0]
            stringlength = self.sizes[1]
            lst = []
            for i in range(sublistcount):
                sublst = []
                for j in range(stringcount):
                    idx = i * stringcount * stringlength + j * stringlength
                    sublst.append(stringlike[idx:idx + stringlength])
                lst.append(sublst)
            return lst

    def index2leafindex(self, idx):
        if len(self.sizes) == 1:
            return idx // self.sizes[0]
        raise NotImplementedError()

    def leafindex2indexpath(self, leafindex):
        if len(self.sizes) == 1:
            return leafindex,
        raise NotImplementedError()

    def indexpath2index(self, indexpath):
        if len(self.sizes) == 1:
            leafindex, = indexpath
            return leafindex * self.sizes[0]
        raise NotImplementedError()

    def __str__(self):
        return "{}({})".format(self.__class__.__name__, self.sizes)
