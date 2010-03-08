from core import Widget
from level import *
from widgets import *
import timing

class GameWidget ( Widget ):
    def __init__(self, level, player, sim, *args, **kwargs):
        Widget.__init__( self, *args, **kwargs )
        self.lastKey = None
        self.name = None
        self.level = level
        self.player = player
        self.sim = sim
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
        screenw, screenh = self.ui.dimensions()
        textfieldheight = 3
        vp = Viewport( level = self.level, window = Subwindow( self.ui, 0, textfieldheight, screenw, screenh - textfieldheight ) )
        vp.paint( self.player.tile.x, self.player.tile.y )
        self.ui.putString( 0, 0, "Time: %lf" % time.time() )
        self.ui.putString( 0, 1, "Your name: %s" % self.name )
    def advanceTime(self, dt):
        self.sim.advance( dt )
        while True:
            ev = self.sim.next()
            if not ev:
                break
            ev.trigger()
    def keyboard(self, key):
        try:
            dx, dy = self.movementKeys[ key ]
            tile = self.player.tile.getRelative( dx, dy )
            if not tile.cannotEnterBecause( self.player ):
                self.player.moveto( tile )
                self.advanceTime( self.player.speed )
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

