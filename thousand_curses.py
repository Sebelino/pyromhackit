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

    def __enter__(self):
        return self

    def make_window(self):
        self.win = curses.newwin(10, 16, 1, 1)
        self.pad = curses.newpad(12, 20)
        curses.curs_set(False)
        for y in range(0, 12):
            for x in range(0, 20):
                try:
                    self.pad.addstr(y, x, chr(ord('a') + (20*y+x) % 26),
                                    curses.color_pair(1))
                except curses.error:
                    pass
        self.pad.addstr(3, 4, 'å', curses.color_pair(2))
        self.pad.addstr(5, 6, 'あ', curses.color_pair(2))
        self.pad.refresh(0, 0, 2, 3, 10, 15)

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
        editor.make_window()
    stdscr.refresh()
    stdscr.getkey()


if __name__ == '__main__':
    curses.wrapper(main)
