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
        self.srcwindow = curses.newwin(height, width, 2, 2)
        self.dstwindow = curses.newwin(height, width, 1, width + 1)

    def __enter__(self):
        return self

    def fill(self):
        h, w = self.srcwindow.getmaxyx()
        for y in range(0, h):
            for x in range(0, w):
                try:
                    self.srcwindow.addstr(y, x, chr(ord('a') + (w*y+x) % 26),
                                          curses.color_pair(1))
                except curses.error:
                    pass
        self.srcwindow.addstr(3, 4, 'å', curses.color_pair(2))
        self.srcwindow.addstr(5, 6, 'あ', curses.color_pair(2))
        self.srcwindow.refresh()

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
        editor.fill()
    stdscr.refresh()
    stdscr.getkey()


if __name__ == '__main__':
    curses.wrapper(main)
