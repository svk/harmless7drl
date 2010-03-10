from core import Widget
from level import *
from widgets import *
from textwrap import TextWrapper
from grammar import *
import timing

class GameWidget ( Widget ):
    def __init__(self, context, *args, **kwargs):
        Widget.__init__( self, *args, **kwargs )
        self.name = None
        self.player = context.player
        context.game = self
        self.context = context
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
        self.restrictVisionByFov = True
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
        fov = self.player.fov( setRemembered = True )
        if self.restrictVisionByFov:
            visibility = lambda tile : (tile.x, tile.y) in fov
        else:
            visibility = lambda tile : True
        vp = Viewport( level = self.player.tile.level,
                       window = Subwindow( self.ui, 0,
                       self.textfieldheight,
                       screenw,
                       screenh - self.textfieldheight ),
                       visibility = visibility
        )
        vp.paint( self.player.tile.x, self.player.tile.y )
        for i in range( self.textfieldheight ):
            try:
                self.ui.putString( 0, i, self.turnlogLines[i] )
            except IndexError:
                pass
    def advanceTime(self, dt):
        self.player.tile.level.sim.advance( dt )
        while True:
            ev = self.player.tile.level.sim.next()
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
        if not tile:
            # At some point I encounteded this. Fairly sure that shouldn't happen.
            print "warning: tile not present"
        else:
            if not tile.cannotEnterBecause( self.player ):
                self.player.moveto( tile )
                self.tookAction( 1 )
            elif tile.isDoor and tile.doorState == "closed":
                self.log( "You open the door." )
                openDoor( tile )
                self.tookAction( 1 )
            else:
                self.log( "You can't move there because %s." % tile.cannotEnterBecause( self.player ) )
    def pickup(self):
        if self.player.tile.items:
            if len( self.player.tile.items ) == 1:
                item = self.player.tile.items.pop()
            else:
                stacked = countItems( self.player.tile.items )
                item = self.main.query( SelectionMenuWidget, choices = [
                    (items[0], name.amount( len(items), informal = True )) for name, items in stacked.items()
                ] + [ (None, "nothing") ], title = "Pick up what?", padding = 5 )
                if not item:
                    return
                self.player.tile.items.remove( item )
            self.player.inventory.append( item )
            self.log( "You pick up %s." % item.name.definite() )
            self.tookAction( 1 )
    def closeDoor(self):
        eligibleDoors = [ n for n in self.player.tile.neighbours() if not cannotCloseDoorBecause(n) ]
        if not eligibleDoors:
            self.log( "There's no open door within reach." )
        else:
            if len( eligibleDoors ) > 1:
                self.log( "Which door?" )
                dx, dy = self.main.query( DirectionWidget )
                door = self.player.tile.getRelative( dx, dy )
                if cannotCloseDoorBecause( door ):
                    self.log( "That's not an open door." )
                    return
            else:
                door = eligibleDoors[-1]
            closeDoor( door )
            self.log( "You close the door." )
            self.tookAction( 1 )
    def goUp(self):
        if self.player.tile.name == "stairs up":
            if self.player.tile.level.previousLevel:
                spot = self.player.tile.level.previousLevel.getPlayerSpawnSpot( upwards = True )
                self.player.moveto( spot )
                self.tookAction( 1 )
            else:
                self.log( "For unspecified plot reasons, you don't want to turn back." )
        else:
            self.log( "You can't see any way to go up right here." )
    def goDown(self):
        if self.player.tile.name == "stairs down":
            if not self.player.tile.level.nextLevel:
                self.player.tile.level.nextLevel = mapFromGenerator( self.context )
                self.player.tile.level.nextLevel.previousLevel = self.player.tile.level
            spot = self.player.tile.level.nextLevel.getPlayerSpawnSpot()
            self.player.moveto( spot )
            self.tookAction( 1 )
        else:
            self.log( "You can't see any way to go down right here." )
    def drop(self):
        if self.player.inventory:
            stacked = countItems( self.player.inventory )
            item = self.main.query( SelectionMenuWidget, choices = [
                (items[0], name.amount( len(items), informal = True )) for name, items in stacked.items()
            ] + [ (None, "nothing") ], title = "Drop what?", padding = 5 )
            if not item:
                return
            item = self.player.inventory.pop()
            self.player.tile.items.append( item )
            self.log( "You drop %s." % item.name.definite() )
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
                'c': self.closeDoor,
                '>': self.goDown,
                '<': self.goUp,
            }[key]
        except KeyError:
            pass
        if standardAction:
            self.clearlog()
            standardAction()
        elif key == 'q':
            self.context.save( "test-savefile.gz" )
            self.done = True
        elif key == 'V':
            self.restrictVisionByFov = not self.restrictVisionByFov
        elif key == 'T':
            newLevel = mapFromGenerator( self.context )
            self.player.moveto( newLevel.getPlayerSpawnSpot() )
        elif key == 'N':
            from widgets import TextInputWidget
            import string
            self.name = self.main.query( TextInputWidget, 32, okay = string.letters, query = "Please enter your name: " )
        elif key == 'M':
            self.main.query( SelectionMenuWidget, [
                (1, "Team Cake"),
                (2, "Team Pie"),
                (3, "Team Edward"),
                (4, "Team Jacob"),
                (5, "Team Bella"),
                (6, "Team Buffy"),
            ], title = "Choose your team", padding = 5)
        elif key == 'S':
            self.context.save( "test-savefile.gz" )
