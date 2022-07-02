from pyromhackit.topology.tree import Topology


class SingletonTopology(Topology):
    def structure(self, stringlike):
        return [stringlike]

    def index2leafindex(self, idx):
        return 0

    def leafindex2indexpath(self, leafindex):
        return 0,

    def indexpath2index(self, indexpath):
        return 0
