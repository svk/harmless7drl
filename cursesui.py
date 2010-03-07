import curses
import sys
import time

def flipyx(yx): return yx[1], yx[0]

class ResizedException:
    pass

class CursesInterface:
    def __init__(self, debug = False):
        self.stdscr = curses.initscr()
        self.debug = debug
        self.setupColours()
        self.setupKeyboard()
        self.previousCursorState = curses.curs_set(0)
        self.warnfile = None
        self.warn( "session start at %s" % (str( time.time())))
    def inside(self, x, y):
        if x < 0 or y < 0:
            return False
        w, h = self.dimensions()
        return not (x >= w or y >= h)
    def dimensions(self):
        return flipyx( self.stdscr.getmaxyx() )
    def clear(self):
        self.stdscr.erase()
    def warn(self, warning):
        if self.debug:
            if not self.warnfile:
                self.warnfile = open( "debug.7drl.txt", "a" )
            print >>self.warnfile, warning
            self.warnfile.flush()
    def setupKeyboard(self):
        curses.halfdelay(1)
        curses.noecho()
        curses.raw()
        self.keymap = {}
        import string
        for ch in string.printable:
            self.keymap[ ord(ch) ] = ch
    def setupColours(self):
        assert curses.has_colors()
        curses.start_color()
        self.colours = {
            'white': curses.COLOR_WHITE,
            'black': curses.COLOR_BLACK,
            'red': curses.COLOR_RED,
        }
        self.pairs = {}
        i = 1
        for fgName,fg in self.colours.items():
            for bgName,bg in self.colours.items():
                curses.init_pair( i, fg, bg )
                self.pairs[ fgName, bgName ] = i
                i += 1
    def put(self, x, y, ch, fg = 'white', bg = 'black'):
        if not self.inside( x, y ):
            self.warn( "put character at %d, %d (out of bounds)" % (x,y) )
        else:
            self.stdscr.addch( y, x, ch, curses.color_pair( self.pairs[ fg, bg ]) )
    def putString(self, x, y, s, fg = 'white', bg = 'black'):
        for ch in s:
            self.put( x, y, ch, fg, bg)
            x += 1
    def show(self):
        self.stdscr.refresh()
    def get(self):
        while True:
            rv = self.stdscr.getch()
            if rv == curses.KEY_RESIZE:
                raise ResizedException()
            try:
                ch = self.keymap[ rv ]
                if ch != None:
                    return ch
            except KeyError:
                self.warn( "unknown input %d" % rv )
    def shutdown(self):
        self.clear()
        curses.endwin()
        curses.curs_set( self.previousCursorState )
        self.warn( "session end at %s" % (str( time.time())))
        if self.warnfile:
            self.warnfile.close()

if __name__ == '__main__':
    try:
        cui = CursesInterface(debug = True)
        w, h = cui.dimensions()
        x, y = 15, 15
        controls = {
            'h': (-1, 0),
            'l': (1, 0),
            'j': (0, 1),
            'k': (0, -1),
            'y': (-1, -1),
            'u': (1, -1),
            'b': (-1, 1),
            'n': (1, 1),
        }
        while True:
            cui.clear()
            cui.putString( 10, 10, "Hello world!" )
            cui.putString( 10, 11, "This window is %dx%d" % (w,h) )
            cui.put( x, y, "@", fg = 'red' )
            rv = None
            try:
                rv = cui.get()
            except ResizedException:
                w, h = cui.dimensions()
            if rv:
                if rv == 'q': break
                if controls.has_key( rv ):
                    dx, dy = controls[ rv ]
                    x += dx
                    y += dy
                    x = max( x, 0 )
                    x = min( x, w - 1 )
                    y = max( y, 0 )
                    y = min( y, h - 1 )
        cui.shutdown()
    except:
        if not curses.isendwin():
            curses.endwin()
        raise
