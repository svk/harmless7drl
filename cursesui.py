import curses
import sys
import time

def main( rootwidget, *args, **kwargs ):
    from core import MainLoop
    rv = None
    try:
        cui = CursesInterface( debug=True )
        rv = MainLoop( cui ).query( rootwidget, *args, **kwargs )
        cui.shutdown()
    except:
        handleException()
    return rv

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
            print >>sys.stderr, warning
    def setupKeyboard(self):
        curses.raw()
        curses.halfdelay(1)
        curses.noecho()
        self.stdscr.keypad( 1 )
        self.keymap = {}
        import string
        for ch in string.printable:
            self.keymap[ ord(ch) ] = ch
        self.keymap[ curses.KEY_BACKSPACE ] = 'backspace'
        self.keymap[ curses.KEY_LEFT ] = 'west'
        self.keymap[ curses.KEY_RIGHT ] = 'east'
        self.keymap[ curses.KEY_UP ] = 'north'
        self.keymap[ curses.KEY_DOWN ] = 'south'
        self.keymap[ curses.KEY_A1 ] = 'northwest'
        self.keymap[ curses.KEY_A3 ] = 'northeast'
        self.keymap[ curses.KEY_C1 ] = 'southwest'
        self.keymap[ curses.KEY_C3 ] = 'southeast'
        del self.keymap[ ord('\t') ] # hack because tab is bound to cause
                                     # trouble in various text input stuff
    def setupColours(self):
        assert curses.has_colors()
        curses.start_color()
        self.colours = {
            'white': (curses.COLOR_WHITE, 0),
            'black': (curses.COLOR_BLACK, 0),
            'red': (curses.COLOR_RED, 0),
            'blue': (curses.COLOR_BLUE, 0),
            'cyan': (curses.COLOR_CYAN, 0),
            'green': (curses.COLOR_GREEN, 0),
            'magenta': (curses.COLOR_MAGENTA, 0),
            'yellow': (curses.COLOR_YELLOW, 0),
            'bold-white': (curses.COLOR_WHITE, curses.A_BOLD),
            'bold-black': (curses.COLOR_BLACK, curses.A_BOLD),
            'bold-red': (curses.COLOR_RED, curses.A_BOLD),
            'bold-blue': (curses.COLOR_BLUE, curses.A_BOLD),
            'bold-cyan': (curses.COLOR_CYAN, curses.A_BOLD),
            'bold-green': (curses.COLOR_GREEN, curses.A_BOLD),
            'bold-magenta': (curses.COLOR_MAGENTA, curses.A_BOLD),
            'bold-yellow': (curses.COLOR_YELLOW, curses.A_BOLD),
        }
        self.pairs = {}
        i = 1
        revs = {}
        for fgName,fga in self.colours.items():
            fg, fgattr = fga
            for bgName,bga in self.colours.items():
                bg, bgattr = bga
                if fg == curses.COLOR_WHITE and bg == curses.COLOR_BLACK:
                    self.pairs[ fgName, bgName ] = 0
                    continue
#                elif fg == bg:
#                    continue
                elif revs.has_key( (fg,bg) ):
                    self.pairs[ fgName, bgName ] = revs[ fg, bg ]
                    continue
                curses.init_pair( i, fg, bg )
                self.pairs[ fgName, bgName ] = i
                revs[ fg, bg ] = i
                i += 1
    def put(self, x, y, ch, fg = 'white', bg = 'black'):
#        if fg == bg:
#            fg = "white" if fg != "white" else "black"
#            ch = ' '
        if not self.inside( x, y ):
            self.warn( "put character at %d, %d (out of bounds)" % (x,y) )
        else:
            try:
                cid, attr = self.colours[ fg ]
                self.stdscr.addch( y, x, ch, curses.color_pair( self.pairs[ fg, bg ]) | attr )
            except:
                # An error is triggered when we write to the last char on the screen?
                pass
    def putString(self, x, y, s, fg = 'white', bg = 'black'):
        for ch in s:
            self.put( x, y, ch, fg, bg)
            x += 1
        return x
    def show(self):
        self.stdscr.refresh()
    def get(self):
        rv = self.stdscr.getch()
        self.warn( "getch returned: %d" % rv )
        if rv == curses.KEY_RESIZE:
            raise ResizedException()
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
        self.warn( "session end at %s" % (str( time.time())))

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
            cui.show()
            rv = None
            try:
                rv = cui.get()
            except ResizedException:
                w, h = cui.dimensions()
            if rv:
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
