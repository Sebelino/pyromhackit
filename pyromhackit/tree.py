#!/usr/bin/env python
import os
from abc import abstractmethod

package_dir = os.path.dirname(os.path.abspath(__file__))


class Topology(object):
    """ A way of transforming a stringlike object into a list of stringlike objects, taking in account only the length
    of the object. """

    @abstractmethod
    def indexpath(self, idx):
        """ For any tree belonging to this Topology, returns the index path to the leaf containing the byte/character
        at index @idx in the flattened (byte-)string. """
        raise NotImplementedError()

    @abstractmethod
    def structure(self, stringlike):
        """ Returns a nested list such that its flattening equals @stringlike, structured according to this Topology. """
        raise NotImplementedError()

    def traverse_preorder(self, stringlike):
        """ Returns a generator for a pair (p, a) where p is the index path from the root of a tree to one of its
        leaves, where the tree belongs this Topology, is flattened into @stringlike, and a is the leaf content. """
        if not stringlike:
            return iter([])
        last_path = self.indexpath(0)
        a = 0
        for i in range(len(stringlike)):
            p = self.indexpath(i)
            if p == last_path:
                continue
            else:
                yield (last_path, stringlike[a:i])
                last_path = p
                a = i

    def length(self, size):
        """ Returns the number of leaves in a tree for a stringlike object of size @size structured according to this
        Topology. """
        count = 0
        lastitem = None
        for item in (self.indexpath(i) for i in range(size)):
            if lastitem != item:
                count += 1
            lastitem = item
        return count

    def __call__(self, *args, **kwargs):
        return self.structure(*args)

    def __str__(self):
        return self.__class__.__name__


class SingletonTopology(Topology):
    def structure(self, stringlike):
        return [stringlike]

    def indexpath(self, idx):
        return 0,


class SimpleTopology(Topology):
    def __init__(self, stringrepr: str):
        """ Encompasses the set of trees that consist of any number of children where each child is either a
        sub(-byte-)string or a subtree with a set structure common for all children. All leaves share the same length.
        @stringrepr is the string representation of a certain Tree structure. @stringrepr is a '-' separated string
        where each token is a positive integer. If the last token is n, each leaf in any Tree belonging to this Topology
        will be a string of length n. If the ith token is n, each subtree at the (i-1)th level of the tree will have
        n children (level zero being the root). """

        self.sizes = [int(t) for t in stringrepr.split("-")]

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
            return [stringlike[i:i+n] for i in range(0, len(stringlike), n)]
        elif len(self.sizes) == 2:
            sublistcount = int(len(stringlike)/self.sizes[0]/self.sizes[1])
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

    def indexpath(self, idx):
        # TODO generalize
        if len(self.sizes) == 1:
            return idx // self.sizes[0],
        if len(self.sizes) == 2:
            cumsizes = [self.sizes[0] * self.sizes[1], self.sizes[1]]
            return idx // cumsizes[0], (idx // cumsizes[1]) % self.sizes[0]
        raise NotImplementedError()

    def __str__(self):
        return "{}({})".format(self.__class__.__name__, self.sizes)
