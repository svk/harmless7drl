from core import Widget
from level import *
from widgets import *

class GameWidget ( Widget ):
    def __init__(self, level, player, *args, **kwargs):
        Widget.__init__( self, *args, **kwargs )
        self.lastKey = None
        self.name = None
        self.level = level
        self.player = player
        self.movementKeys = {
            'h': (-1, 0),
            'l': (1, 0),
            'j': (0, 1),
            'k': (0, -1),
            'y': (-1, -1),
            'u': (1, -1),
            'b': (-1, 1),
            'n': (1, 1),
            'west': (-1, 0),
            'east': (1, 0),
            'south': (0, 1),
            'north': (0, -1),
            'northwest': (-1, -1),
            'northeast': (1, -1),
            'southwest': (-1, 1),
            'southeast': (1, 1),
        }
    def draw(self):
        import time
        vp = Viewport( level = self.level, window = Subwindow( self.ui, 0, 0, *self.ui.dimensions() ) )
        vp.paint( self.player.tile.x, self.player.tile.y )
        self.ui.putString( 30, 10, "Hello world!" )
        self.ui.putString( 30, 11, "Time: %lf" % time.time() )
        self.ui.putString( 30, 12, "Last keypress: %s" % self.lastKey )
        self.ui.putString( 30, 13, "Your name: %s" % self.name )
    def keyboard(self, key):
        try:
            dx, dy = self.movementKeys[ key ]
            tile = self.player.tile.getRelative( dx, dy )
            if not tile.cannotEnterBecause( self.player ):
                self.player.moveto( tile )
            return
        except KeyError:
            pass
        if key == 'q':
            self.done = True
        if key == 'N':
            from widgets import TextInputWidget
            import string
            self.name = self.main.query( TextInputWidget, 32, okay = string.letters, query = "Please enter your name: " )
        self.lastKey = key

