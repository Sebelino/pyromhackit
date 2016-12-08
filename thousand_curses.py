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
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)

        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(1)

    def __enter__(self):
        return self

    def make_window(self):
        self.win = curses.newwin(10, 16, 0, 0)
        self.pad = curses.newpad(100, 100)
        for y in range(0, 100):
            for x in range(0, 100):
                try:
                    self.pad.addch(y, x, ord('a') + (x*x+y*y) % 26,
                                   curses.color_pair(1))
                except curses.error:
                    pass
        self.pad.refresh(0, 0, 2, 3, 10, 15)

    def sleep(self, seconds):
        time.sleep(seconds)

    def __exit__(self, exec_type, exec_value, traceback):
        curses.nocbreak()
        self.stdscr.keypad(0)
        curses.echo()
        curses.endwin()


if __name__ == '__main__':
    with Editor() as editor:
        editor.make_window()
        editor.sleep(3)
