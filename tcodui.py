import libtcodpy as libtcod
import time

def main( rootwidget, *args, **kwargs ):
    from harmless7drl import MainLoop, windowsSetIcon
    rv = None
    windowsSetIcon()
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
        from harmless7drl import getCfg
        self.width = getCfg( "tcod", "width", 100, int )
        self.height = getCfg( "tcod", "height", 60, int )
        self.fps_limit = 20
        self.font_name = getCfg( "tcod", "font", "harmless-font.png" )
        self.font_layout = {
            "tcod":  libtcod.FONT_LAYOUT_TCOD,
            "ascii_incol":  libtcod.FONT_LAYOUT_ASCII_INCOL,
            "ascii_inrow":  libtcod.FONT_LAYOUT_ASCII_INROW,
        }[getCfg( "tcod", "fontlayout", "tcod" )]
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
        for key in self.colours.keys():
            self.colours["bold-"+key] = self.colours[key]
        for key in self.colours:
            if "bold" not in key:
                c = self.colours[key]
                self.colours[key] = libtcod.Color( c.r & 0x80, c.g & 0x80, c.b & 0x80 )
        from widgets import PrimaryColourRGB, SecondaryColourRGB, BorderColourRGB, HighlightPrimaryColourRGB, HighlightSecondaryColourRGB
        self.colours[ "tcod-primary" ] = libtcod.Color( *PrimaryColourRGB )
        self.colours[ "tcod-secondary" ] = libtcod.Color( *SecondaryColourRGB )
        self.colours[ "tcod-primary-hl" ] = libtcod.Color( *HighlightPrimaryColourRGB )
        self.colours[ "tcod-secondary-hl" ] = libtcod.Color( *HighlightSecondaryColourRGB )
        self.colours[ "tcod-border" ] = libtcod.Color( *BorderColourRGB )
        self.colours["bold-black"] = libtcod.Color( 0x80, 0x80, 0x80 )
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
            libtcod.KEY_ENTER: '\n',
            libtcod.KEY_ESCAPE: 'escape',
        }
        libtcod.console_set_custom_font( self.font_name,
                                         libtcod.FONT_TYPE_GREYSCALE | self.font_layout)
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
    def putString(self, x, y, s, fg = 'white', bg = 'black'):
        for ch in s:
            self.put( x, y, ch, fg, bg)
            x += 1
        return x
    def shutdown(self):
        pass
    def clear(self):
        libtcod.console_set_foreground_color( 0, self.colours[ 'black' ] )
        libtcod.console_set_background_color( 0, self.colours[ 'black' ] )
        libtcod.console_clear(0)
    def put(self, x, y, ch, fg = 'white', bg = 'black'):
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
