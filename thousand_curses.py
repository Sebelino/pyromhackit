#!/usr/bin/env python

""" Ncurses ROM editor """

import curses
import curses.textpad
import time
import argparse
import shutil
import codec


class Editor:
    """ The complete Ncurses editor """
    def __init__(self, romfile):
        self.stdscr = curses.initscr()
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_YELLOW)
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_BLUE)

        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(1)
        curses.curs_set(True)

        width = 16
        height = 10
        self.windows = {
            'src': curses.newwin(height, width, 1, 1),
            'dst': curses.newwin(height, width, 1, width + 2),
        }
        self.windows['src'].bkgd(' ', curses.color_pair(1))
        self.windows['dst'].bkgd(' ', curses.color_pair(3))
        self.raw = romfile.read()
        self.windows['src'].addstr(0, 0, codec.Hexify.decode(self.raw))
        self.windows['dst'].addstr(0, 0, codec.MajinTenseiII.decode(self.raw))
        self.textboxes = {
            'src': curses.textpad.Textbox(self.windows['src'],
                                          insert_mode=False),
            'dst': curses.textpad.Textbox(self.windows['dst'],
                                          insert_mode=True),
        }
        self.windows['dst'].putwin(open('dst.out', 'wb'))

    def __enter__(self):
        return self

    def fill(self, window):
        h, w = self.windows[window].getmaxyx()
        for y in range(0, h):
            for x in range(0, w):
                try:
                    ch = chr(ord('a') + (w*y+x) % 26)
                    self.windows[window].addstr(y, x, ch, curses.color_pair(1))
                except curses.error:
                    pass
        self.windows[window].addstr(3, 4, 'å', curses.color_pair(2))
        self.windows[window].addstr(5, 6, 'あ', curses.color_pair(2))

    def _sync(self):
        """ Sync dst window to src window """

    def edit(self):
        return self.textboxes['dst'].edit()

    def refresh(self):
        for w in self.windows:
            self.windows[w].refresh()

    def sleep(self, seconds):
        time.sleep(seconds)

    def __exit__(self, exec_type, exec_value, traceback):
        curses.nocbreak()
        self.stdscr.keypad(0)
        curses.echo()
        curses.endwin()


def main(stdscr, rom):
    stdscr.clear()
    with Editor(rom) as editor:
        editor.refresh()
        text = editor.edit()
        print(text, file=open('editor_edit.out', 'w'))
    stdscr.refresh()
    #stdscr.getkey()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="ncurses-based ROM viewer and editor"
    )
    parser.add_argument("romfile", help="Path to your ROM file.")
    # TODO Validate rom_file is a path to an existing file (not dir)
    args = parser.parse_args()
    shutil.copy(args.romfile, "{}.bak".format(args.romfile))
    curses.wrapper(main, open(args.romfile, 'rb'))
