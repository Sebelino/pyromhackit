#!/usr/bin/env python

import os

import treelib
from queue import Queue

package_dir = os.path.dirname(os.path.abspath(__file__))


class Tree(treelib.Tree):
    def __init__(self, arg):
        self.from_nested_container(arg)

    def from_nested_container(self, arg):
        if not self.is_treelike(arg):
            raise ValueError(
                "A tree is constructed from a non-empty nested iterable of iterables, strings, or bytestrings."
                " The presence of a string is mutually exclusive with the presence of a bytestring.")
        self.create_node(tag="test", identifier="id", parent=None, data=None)
        container_types = {tuple, list, Tree}
        self.type = None
        for c in arg:
            is_container = any(isinstance(c, tpe) for tpe in container_types)
            if is_container:
                infant = Tree(c)
                self.children.append(infant)
            else:
                self.children.append(c)
        typeset = {c.type if isinstance(c, Tree) else type(c) for c in self.children}
        self.type = typeset.pop()

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
