import libtcodpy as libtcod
import time

def main( rootwidget, *args, **kwargs ):
    from core import MainLoop
    rv = None
    try:
        tui = TcodInterface( debug = True )
        rv = MainLoop( tui ).query( rootwidget, *args, **kwargs )
    except WindowClosedException:
        pass
    return rv

class KeypressEvent:
    def __init__(self, key):
        self.type = "keypress"
        self.key = key

class WindowClosedException:
    pass

class TcodInterface:
    def __init__(self, debug = False):
        self.width = 60
        self.height = 60
        self.fps_limit = 20
        self.font_name = 'arial10x10.png'
        self.title = 'Harmless7DRL'
        self.colours = {
            'white': libtcod.white,
            'black': libtcod.black,
            'red': libtcod.red,
            'blue': libtcod.blue,
            'cyan': libtcod.cyan,
            'green': libtcod.green,
            'magenta': libtcod.magenta,
            'yellow': libtcod.yellow,
        }
        self.keymap = {
            libtcod.KEY_BACKSPACE: 'backspace',
            libtcod.KEY_KP1: 'southwest',
            libtcod.KEY_KP2: 'south',
            libtcod.KEY_KP3: 'southeast',
            libtcod.KEY_KP4: 'west',
            libtcod.KEY_KP6: 'east',
            libtcod.KEY_KP7: 'northwest',
            libtcod.KEY_KP8: 'north',
            libtcod.KEY_KP9: 'northeast',
            libtcod.KEY_END: 'southwest',
            libtcod.KEY_DOWN: 'south',
            libtcod.KEY_PAGEDOWN: 'southeast',
            libtcod.KEY_LEFT: 'west',
            libtcod.KEY_RIGHT: 'east',
            libtcod.KEY_HOME: 'northwest',
            libtcod.KEY_UP: 'north',
            libtcod.KEY_PAGEUP: 'northeast',
        }
        libtcod.console_set_custom_font( self.font_name,
                                         libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
        libtcod.console_init_root(self.width, self.height, self.title, False)
        libtcod.sys_set_fps( self.fps_limit )
    def dimensions(self):
        return self.width, self.height
    def warn(self, warning):
        pass # OMGWTFBBQ
    def show(self):
        libtcod.console_flush()
    def inside(self, x, y):
        if x < 0 or y < 0:
            return False
        w, h = self.dimensions()
        return not (x >= w or y >= h)
    def putString(self, x, y, s, fg = 'white', bg = 'black', attrs = 0):
        for ch in s:
            self.put( x, y, ch, fg, bg, attrs)
            x += 1
    def shutdown(self):
        pass
    def clear(self):
        libtcod.console_set_foreground_color( 0, self.colours[ 'black' ] )
        libtcod.console_set_background_color( 0, self.colours[ 'black' ] )
        libtcod.console_clear(0)
    def put(self, x, y, ch, fg = 'white', bg = 'black', attrs = 0):
        libtcod.console_set_foreground_color( 0, self.colours[ fg ] )
        libtcod.console_set_background_color( 0, self.colours[ bg ] )
        libtcod.console_put_char( 0, x, y, ch, libtcod.BKGND_SET )
    def get(self):
        if libtcod.console_is_window_closed():
            raise WindowClosedException()
        rv = libtcod.console_check_for_keypress( libtcod.KEY_PRESSED )
        if rv.vk == libtcod.KEY_NONE:
            time.sleep( 0.01 )
            return None
        try:
            ch = self.keymap[ rv.vk ]
            if ch != None:
                return KeypressEvent( ch )
        except KeyError:
            if rv.c > 0:
                return KeypressEvent( chr( rv.c ) )
        return None

if __name__ == '__main__':
    try:
        cui = TcodInterface(debug = True)
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
            rv = cui.get()
            cui.show()
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
        raise
