#!/usr/bin/env python

""" Ncurses ROM editor """

import curses
import time


class Editor:
    """ The complete Ncurses editor """
    def __init__(self):
        self.stdscr = curses.initscr()
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_RED)
        curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_YELLOW)

        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(1)
        curses.curs_set(False)

        width = 16
        height = 10
        self.windows = {
            'src': curses.newwin(height, width, 1, 1),
            'dst': curses.newwin(height, width, 1, width + 2),
        }

    def __enter__(self):
        return self

    def fill(self, window):
        h, w = self.windows[window].getmaxyx()
        for y in range(0, h):
            for x in range(0, w):
                try:
                    self.windows[window].addstr(y, x, chr(ord('a') + (w*y+x) %
                                                          26),
                                                curses.color_pair(1))
                except curses.error:
                    pass
        self.windows[window].addstr(3, 4, 'å', curses.color_pair(2))
        self.windows[window].addstr(5, 6, 'あ', curses.color_pair(2))

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


def main(stdscr):
    stdscr.clear()
    with Editor() as editor:
        editor.fill('src')
        editor.fill('dst')
        editor.refresh()
    stdscr.refresh()
    stdscr.getkey()


if __name__ == '__main__':
    curses.wrapper(main)
