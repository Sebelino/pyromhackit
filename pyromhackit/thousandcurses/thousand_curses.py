#!/usr/bin/env python

""" Ncurses ROM editor """

import curses
import curses.textpad
import argparse
import shutil

from editor import Editor


def dump(text):
    """ Useful for quick and dirty ncurses debugging. """
    with open("debug.out", 'w') as f:
        f.write(str(text))


class ThousandCurses(object):
    """ The ncurses UI for the editor. """
    def __init__(self, romfile, cdc):
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

        self.editor = Editor(romfile, 32, 40, cdc)
        self.width = self.editor.width    # Convenient alias
        self.height = self.editor.height  # Convenient alias
        self.windows = {
            'src': curses.newwin(self.height, self.width, 1, 1),
            'dst': curses.newwin(self.height, self.width, 1, self.width + 2),
        }
        self.windows['src'].bkgd(' ', curses.color_pair(1))
        self.windows['dst'].bkgd(' ', curses.color_pair(3))
        self.windows['src'].addstr(0, 0, self.editor.windows['src'])
        self.windows['dst'].addstr(0, 0, self.editor.windows['dst'])
        self.textboxes = {
            'src': curses.textpad.Textbox(self.windows['src'],
                                          insert_mode=False),
            'dst': curses.textpad.Textbox(self.windows['dst'],
                                          insert_mode=True),
        }
        self.textboxes['src'].stripspaces = 0
        self.textboxes['dst'].stripspaces = 0
        self.windows['dst'].putwin(open('dst.out', 'wb'))

    def do_command(self, ch):
        """ :param ch: Input character. """
        if ch == curses.ascii.BEL:
            return ch
        elif ch == curses.KEY_UP:
            self.editor.scroll(-1, 'src')
            self.refresh()
        elif ch == curses.KEY_DOWN:
            self.editor.scroll(1, 'src')
            self.refresh()

    def __enter__(self):
        return self

    def fill(self, window):
        """ Fill the window with random gibberish. """
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
        return self.textboxes['dst'].edit(self.do_command)

    def refresh(self):
        content = self.editor.windows['dst']
        self.windows['dst'].addstr(0, 0, content)
        for w in self.windows:
            self.windows[w].refresh()

    def exit(self):
        self.__exit__(None, None, None)

    def __exit__(self, exec_type, exec_value, traceback):
        curses.nocbreak()
        self.stdscr.keypad(0)
        curses.echo()
        curses.endwin()


def main(stdscr, rom, cdc):
    stdscr.clear()
    with ThousandCurses(rom, cdc) as tcurses:
        tcurses.refresh()
        text = tcurses.edit()
        print(text, file=open('editor_edit.out', 'w'))
    stdscr.refresh()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="ncurses-based ROM viewer and editor"
    )
    parser.add_argument("romfile", help="Path to your ROM file.")
    parser.add_argument("codec", help="Name of the codec used. Check codec.py.")
    # TODO Validate rom_file is a path to an existing file (not dir)
    args = parser.parse_args()
    shutil.copy(args.romfile, "{}.bak".format(args.romfile))
    curses.wrapper(main, open(args.romfile, 'rb'), args.codec)
