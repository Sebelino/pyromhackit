#!/usr/bin/env python

import os

package_dir = os.path.dirname(os.path.abspath(__file__))


class Topology(object):
    def __init__(self, stringrepr: str):
        """ @stringrepr is the string representation of a certain Tree structure. @stringrepr is a '-' separated string
        where each token is either a positive integer or the character '*'. If the ith token is an integer n, each
        subtree in the (i-1)th level of any Tree belonging to this Topology will contain n children. If the token is
        '*', the ith level will consist of any number of nodes. You can use this class to create a Tree from a
        (byte-)string. """

        self.sizes = [None if t == '*' else int(t) for t in stringrepr.split("-")]
        assert self.sizes[0] is None  # Assuming the form *...-n for now
        for s in self.sizes[1:]:
            assert isinstance(s, int)

    def maketree(self, iterable):
        if len(self.sizes) == 1:
            return iterable
        elif len(self.sizes) == 2:
            lst = list(iterable)
            s = self.sizes[1]
            return list(zip(list(lst[i::s]) for i in range(s)))

    def indexpath(self, i):
        """ Returns the index path to the ith child for any Tree belonging to this Topology. """
        cumsizes = [None] + [sum(self.sizes[i:]) for i in range(1, len(self.sizes))]
        path = []
        for j in range(1, len(self.sizes)):
            childidx = i % cumsizes[j]
            path.append(childidx)
        return tuple(path)

    def __str__(self):
        return "{}({})".format(self.__class__.__name__, self.sizes)
