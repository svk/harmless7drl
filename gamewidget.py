from core import Widget
from level import *
from widgets import *
from textwrap import TextWrapper
import timing

class GameWidget ( Widget ):
    def __init__(self, level, context, *args, **kwargs):
        Widget.__init__( self, *args, **kwargs )
        self.name = None
        self.level = level
        self.player = context.player
        self.sim = context.sim
        context.game = self
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
        self.textfieldheight = 4
        screenw, screenh = self.ui.dimensions()
        self.turnlogWrapper = TextWrapper( screenw, self.textfieldheight )
        self.turnlogLines = []
    def log(self, s):
        self.turnlogWrapper.feed( s + " " )
        while self.turnlogWrapper.pages:
            self.turnlogLines = self.turnlogWrapper.popPage()
            self.main.query( HitEnterWidget )
        self.turnlogLines = []
        for i in range(self.textfieldheight):
            self.turnlogLines.append( self.turnlogWrapper.line(i) )
    def resized(self, screenw, screenh):
        # quirk: will lose data in text field when resizing
        self.turnlogWrapper = TextWrapper( screenw, self.textfieldheight )
    def clearlog(self):
        screenw, screenh = self.ui.dimensions()
        self.turnlogWrapper = TextWrapper( screenw, self.textfieldheight )
        self.turnlogLines = []
    def draw(self):
        import time
        screenw, screenh = self.ui.dimensions()
        fov = self.player.fov()
        vp = Viewport( level = self.level, window = Subwindow( self.ui, 0, self.textfieldheight, screenw, screenh - self.textfieldheight ), visibility = lambda tile : (tile.x, tile.y) in fov )
        vp.paint( self.player.tile.x, self.player.tile.y )
        for i in range( self.textfieldheight ):
            try:
                self.ui.putString( 0, i, self.turnlogLines[i] )
            except IndexError:
                pass
    def advanceTime(self, dt):
        self.sim.advance( dt )
        while True:
            ev = self.sim.next()
            if not ev:
                break
            ev.trigger()
    def tookAction(self, weight):
        self.advanceTime( self.player.speed * weight )
    def wait(self):
        self.log( "You wait." )
        self.tookAction( 1 )
    def tryMoveAttack(self, dx, dy):
        tile = self.player.tile.getRelative( dx, dy )
        if not tile.cannotEnterBecause( self.player ):
            self.player.moveto( tile )
            self.tookAction( 1 )
        else:
            self.log( "You can't move there because %s." % tile.cannotEnterBecause( self.player ) )
    def pickup(self):
        if self.player.tile.items:
            if len( self.player.tile.items ) == 1:
                item = self.player.tile.items.pop()
            else:
                item = self.main.query( SelectionMenuWidget, choices = [
                    (item, item.name) for item in self.player.tile.items
                ] + [ (None, "nothing") ], title = "Pick up which item?", padding = 5 )
                if not item:
                    return
                self.player.tile.items.remove( item )
            self.player.inventory.append( item )
            self.log( "You pick up the %s." % (item.name) )
            self.tookAction( 1 )
    def drop(self):
        if self.player.inventory:
            item = self.main.query( SelectionMenuWidget, choices = [
                (item, item.name) for item in self.player.inventory
            ] + [ (None, "nothing") ], title = "Drop which item?", padding = 5 )
            if not item:
                return
            item = self.player.inventory.pop()
            self.player.tile.items.append( item )
            self.log( "You drop the %s." % item.name )
            self.tookAction( 1 )
    def keyboard(self, key):
        try:
            dx, dy = self.movementKeys[ key ]
            self.clearlog()
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
            self.clearlog()
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
        elif key == 'M':
            self.main.query( SelectionMenuWidget, [
                (1, "Team Cake"),
                (2, "Team Pie"),
                (3, "Team Edward"),
                (4, "Team Jacob"),
                (5, "Team Bella"),
                (6, "Team Buffy"),
            ], title = "Choose your team", padding = 5)
