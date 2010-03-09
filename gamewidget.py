from core import Widget
from level import *
from widgets import *
import timing

class GameWidget ( Widget ):
    def __init__(self, level, player, sim, *args, **kwargs):
        Widget.__init__( self, *args, **kwargs )
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
        self.playervision = None
    def draw(self):
        import time
        screenw, screenh = self.ui.dimensions()
        textfieldheight = 3
        if not self.playervision:
            from vision import VisionField
            self.playervision = VisionField( self.player.tile, lambda tile: tile.impassable)
        vp = Viewport( level = self.level, window = Subwindow( self.ui, 0, textfieldheight, screenw, screenh - textfieldheight ), visibility = lambda tile : (tile.x, tile.y) in self.playervision.visible )
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
    def tookAction(self, weight):
        self.advanceTime( self.player.speed * weight)
    def wait(self):
        self.tookAction( 1 )
    def tryMoveAttack(self, dx, dy):
        tile = self.player.tile.getRelative( dx, dy )
        if not tile.cannotEnterBecause( self.player ):
            self.playervision = None
            self.player.moveto( tile )
            self.tookAction( 1 )
    def pickup(self):
        if self.player.tile.items:
            item = self.player.tile.items.pop()
            self.player.inventory.append( item )
            self.tookAction( 1 )
    def drop(self):
        if self.player.inventory:
            item = self.player.inventory.pop()
            self.player.tile.items.append( item )
            self.tookAction( 1 )
    def keyboard(self, key):
        try:
            dx, dy = self.movementKeys[ key ]
            self.tryMoveAttack( dx, dy )
            return
        except KeyError:
            pass
        try:
            standardAction = None
            standardAction = {
                '.': self.wait,
                ',': self.pickup,
                'd': self.drop,
            }[key]
        except KeyError:
            pass
        if standardAction:
            standardAction()
        elif key == 'q':
            self.done = True
        elif key == 'N':
            from widgets import TextInputWidget
            import string
            self.name = self.main.query( TextInputWidget, 32, okay = string.letters, query = "Please enter your name: " )
        elif key == 'P':
            from pathfind import Pathfinder, infinity
            import math
            pf = Pathfinder(cost = lambda tile : infinity if tile.cannotEnterBecause( self.player ) else 1,
                            goal = lambda tile : tile.x == 5 and tile.y == 5,
                            heuristic = lambda tile : max( abs( tile.x - 5 ), abs( tile.y - 5 ) )
            )
            pf.addOrigin( self.player.tile )
            path = pf.seek()
            if path:
                for tile in path:
                    tile.fgColour = "blue"
