from pyromhackit.topology.topology import Topology


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
        return "{}({})".format(self.__class__.__name__, *self.sizes)
