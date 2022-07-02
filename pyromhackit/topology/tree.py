#!/usr/bin/env python
import os
from abc import abstractmethod, ABCMeta
from collections import namedtuple

package_dir = os.path.dirname(os.path.abspath(__file__))


class Topology(metaclass=ABCMeta):
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
            yield Leaf(idx, leafidx, idxpath, self.getleaf(leafidx, stringlike))

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
