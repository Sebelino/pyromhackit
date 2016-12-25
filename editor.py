#!/usr/bin/env python

""" Ncurses ROM editor """

import codec


class Editor(object):
    """ The elements of the editor which do not depend on ncurses. """
    def __init__(self, romfile, width, height):
        self.raw = romfile.read()
        self.width = width
        self.height = height
        self.pad = {
            'src': codec.Hexify.decode(self.raw),
            'dst': codec.Mt2GarbageTextPair.decode(self.raw),
        }
        self.topline = 1
        self.refresh()

    def scroll(self, number_of_lines, window):
        if self.topline+number_of_lines < 1:
            return
        if self.topline+number_of_lines > len(self.raw)/self.width:
            return
        self.topline = self.topline+number_of_lines
        self.refresh()

    def refresh(self):
        a = (self.topline-1)*self.width
        b = (self.topline-1)*self.width+int(self.width*self.height/2)
        self.windows = {
            'src': self.pad['src'][a:b],
            'dst': self.pad['dst'][a:b],
        }
