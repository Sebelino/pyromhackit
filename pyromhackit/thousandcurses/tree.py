#!/usr/bin/env python

import os

import treelib

package_dir = os.path.dirname(os.path.abspath(__file__))


class Tree(treelib.Tree):
    def __init__(self):
        self.create_node()
    pass
