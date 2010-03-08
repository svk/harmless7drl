import curses
import sys
import time

def handleException():
    if not curses.isendwin():
        curses.endwin()
    raise

def flipyx(yx): return yx[1], yx[0]

class KeypressEvent:
    def __init__(self, key):
        self.type = "keypress"
        self.key = key

from core import ResizedException

class CursesInterface:
    def __init__(self, debug = False):
        self.stdscr = curses.initscr()
        self.debug = debug
        self.setupColours()
        self.setupKeyboard()
        self.previousCursorState = curses.curs_set(0)
        self.warnfile = None
        self.warn( "session start at %s" % (str( time.time())))
        avail, self.previousMouseMask = curses.mousemask( curses.BUTTON1_PRESSED )
        self.warn( "mouse mask reported %d" % avail )
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
        curses.raw()
        curses.halfdelay(1)
        curses.noecho()
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
            'blue': curses.COLOR_BLUE,
            'cyan': curses.COLOR_CYAN,
            'green': curses.COLOR_GREEN,
            'magenta': curses.COLOR_MAGENTA,
            'yellow': curses.COLOR_YELLOW,
        }
        self.pairs = {}
        i = 1
        for fgName,fg in self.colours.items():
            for bgName,bg in self.colours.items():
                if fg == curses.COLOR_WHITE and bg == curses.COLOR_BLACK:
                    self.pairs[ fgName, bgName ] = 0
                elif fg == bg:
                    continue
                curses.init_pair( i, fg, bg )
                self.pairs[ fgName, bgName ] = i
                i += 1
    def put(self, x, y, ch, fg = 'white', bg = 'black', attrs = 0):
        if fg == bg:
            fg = "white" if fg != "white" else "black"
            ch = ' '
        if not self.inside( x, y ):
            self.warn( "put character at %d, %d (out of bounds)" % (x,y) )
        else:
            try:
                self.stdscr.addch( y, x, ch, curses.color_pair( self.pairs[ fg, bg ]) | attrs )
            except:
                # An error is triggered when we write to the last char on the screen?
                pass
    def putString(self, x, y, s, fg = 'white', bg = 'black', attrs = 0):
        for ch in s:
            self.put( x, y, ch, fg, bg, attrs)
            x += 1
    def show(self):
        self.stdscr.refresh()
    def get(self):
        rv = self.stdscr.getch()
        if rv == curses.KEY_RESIZE:
            raise ResizedException()
        if rv == curses.KEY_MOUSE:
            id, x, y, z, bstate = curses.getmouse()
        try:
            ch = self.keymap[ rv ]
            if ch != None:
                return KeypressEvent( ch )
        except KeyError:
            self.warn( "unknown input %d" % rv )
        return None
    def shutdown(self):
        self.clear()
        curses.endwin()
        curses.curs_set( self.previousCursorState )
        curses.mousemask( self.previousMouseMask )
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
            cui.putString( 10, 13, "longname(): %s" % curses.longname() )
            cui.putString( 10, 14, "COLOR_PAIRS: %d" % curses.COLOR_PAIRS )
            cui.putString( 10, 15, "can_change_color(): %s" % curses.can_change_color() )
            cui.put( x, y, "@", fg = 'red' )
            rv = None
            try:
                rv = cui.get()
            except ResizedException:
                w, h = cui.dimensions()
            if rv.type == "keypress":
                if rv.key == 'q': break
                if controls.has_key( rv.key ):
                    dx, dy = controls[ rv.key ]
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
