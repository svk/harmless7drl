# This module is definitely misnamed; in addition to level data it contains
# the Mobile class and the Item class, as well as the viewport that
# displays the map on screen.

# It does not and will not contain the level generator.

import random
from timing import Speed
import timing

def countItems( l ):
    rv = {}
    for item in l:
        try:
            rv[item.name].append( item )
        except KeyError:
            rv[item.name] = [item]
    return rv

class Tile:
    # Yes, keeping each tile in its own object, because I intend to do funky
    # stuff with the environment.
    def __init__(self, context, level, x, y):
        self.name = "null" # e.g. "floor", "wall"
        self.symbol = "?"
        self.fgColour = "white"
        self.bgColour = "black" # be careful setting this, need contrast
        self.impassable = True
        self.mobile = None
        self.spawnItems = False
        self.spawnMonsters = False
        self.hindersLOS = True
        self.level = level
        self.isDoor = False
        self.context = context
        self.remembered = False
        self.x, self.y = x, y
        self.items = []
    def cannotEnterBecause(self, mobile):
        if self.impassable:
            return "tile is impassable"
        if self.mobile != None:
            return "there's something in the way"
        return ""
    def leaves(self):
        self.mobile = None
    def enters(self, mobile):
        # Appropriate place for trap triggers etc.
        self.mobile = mobile
    def appearance(self):
        rv = {
            'ch': self.symbol,
            'fg': self.fgColour,
            'bg': self.bgColour,
        }
        if self.items:
            mergeAppearance( rv, self.items[-1].appearance() )
        if self.mobile:
            mergeAppearance( rv, self.mobile.appearance() )
        return rv
    def appearanceRemembered(self):
        return {
            'ch': self.symbol,
            'fg': self.fgColour,
            'bg': self.bgColour,
        }
    def getRelative(self, dx, dy):
        return self.level.get( self.x + dx, self.y + dy )
    def neighbours(self):
        return [ self.getRelative(dx,dy) for dx in (-1,0,1) for dy in (-1,0,1) if dx or dy ]
    def describeHere(self):
        import grammar
        if self.items:
            ent = []
            stacked = countItems( self.items )
            ent.append( grammar.makeCountingList( stacked ) )
            if len( self.items ) > 1:
                ent.append( "are" )
            else:
                ent.append( "is" )
            ent.append( "here." )
            self.context.log( grammar.capitalizeFirst( " ".join( ent ) ) )
    def opaque(self):
        if self.mobile and self.mobile.hindersLOS:
            return True
        return self.hindersLOS
    def remember(self):
        self.remembered = True

def cannotCloseDoorBecause( tile ):
    if not tile.isDoor:
        return "there's no door there"
    if tile.doorState != "open":
        return "it's already closed"
    if tile.items:
        return "there's something in the way"
    if tile.mobile:
        return "there's a creature in the way"
    return ""

def closeDoor( tile ):
    assert not cannotCloseDoorBecause( tile )
    makeClosedDoor( tile )

def openDoor( tile ):
    # this is done by bumping so we don't need error messages
    assert tile.isDoor
    makeOpenDoor( tile )

def makeStairsDown( tile ):
    tile.name = "stairs down"
    tile.symbol = ">"
    tile.fgColour = "white"
    tile.bgColour = "black"
    tile.impassable = False
    tile.spawnMonsters = False
    tile.spawnItems = False
    tile.level.stairsDown = tile
    
def makeStairsUp( tile ):
    tile.name = "stairs up"
    tile.symbol = "<"
    tile.fgColour = "white"
    tile.bgColour = "black"
    tile.impassable = False
    tile.spawnMonsters = False
    tile.spawnItems = False
    tile.level.stairsUp = tile

def makeImpenetrableRock( tile ):
    tile.name = "rock"
    tile.symbol = " "
    tile.fgColour = "white"
    tile.bgColour = "black"
    tile.impassable = True
    tile.spawnMonsters = False
    tile.spawnItems = False
    tile.hindersLOS = True

def makeClosedDoor( tile ):
    tile.name = "closed door"
    tile.symbol = "+"
    tile.fgColour = "black"
    tile.bgColour = "yellow"
    tile.impassable = True
    tile.spawnMonsters = False
    tile.spawnItems = False
    tile.hindersLOS = True
    tile.isDoor = True
    tile.doorState = "closed"

def makeOpenDoor( tile ):
    tile.name = "open door"
    tile.symbol = "+"
    tile.fgColour = "yellow"
    tile.bgColour = "black"
    tile.impassable = False
    tile.spawnMonsters = False
    tile.spawnItems = False
    tile.hindersLOS = False
    tile.isDoor = True
    tile.doorState = "open"

def makeHallway( tile ):
    tile.name = "passage floor"
    tile.symbol = "."
    tile.fgColour = "white"
    tile.bgColour = "black"
    tile.impassable = False
    tile.spawnMonsters = False
    tile.spawnItems = False
    tile.hindersLOS = False

def makeFloor( tile ):
    tile.name = "floor"
    tile.symbol = "."
    tile.fgColour = "white"
    tile.bgColour = "black"
    tile.impassable = False
    tile.spawnMonsters = True
    tile.spawnItems = True
    tile.hindersLOS = False

def makeWall( tile ):
    tile.name = "wall"
    tile.symbol = "#"
    tile.fgColour = "white"
    tile.bgColour = "black"
    tile.impassable = True
    tile.spawnMonsters = False
    tile.spawnItems = False
    tile.hindersLOS = True

class Mobile:
    def __init__(self, tile, name, symbol, speed = Speed.Normal, ai = None, context = None, fgColour = 'white', bgColour = None, noSchedule = False, hindersLOS = False):
        self.name = name
        self.hindersLOS = hindersLOS
        self.context = context
        self.symbol = symbol
        self.fgColour = fgColour
        self.bgColour = bgColour
        self.tile = None
        self.scheduledAction = None
        self.speed = speed
        self.ai = ai
        self.sim = tile.level.sim
        self.inventory = []
        self.noSchedule = noSchedule
        self.moveto( tile )
        self.schedule()
    def moveto(self, tile):
        assert not tile.cannotEnterBecause( self )
        if self.tile:
            self.tile.leaves()
        if not self.tile or self.tile.level != tile.level:
            if self.scheduledAction:
                self.scheduledAction.cancel()
            self.tile = tile
            self.schedule()
        else:
            self.tile = tile
        self.tile.enters( self )
        if self.isPlayer():
            self.tile.describeHere()
    def isPlayer(self):
        try:
            return self.context.player == self
        except AttributeError:
            return False
    def appearance(self):
        rv = {
            'ch': self.symbol,
            'fg': self.fgColour
        }
        if self.bgColour:
            rv[ 'bg' ] = self.bgColour
        return rv
    def schedule(self):
        if not self.noSchedule:
            self.tile.level.sim.schedule( self, self.sim.t + self.speed )
    def trigger(self, t):
        if self.ai:
            self.ai.trigger( self )
        self.tile.level.sim.schedule( self, t + self.speed )
    def fov(self, radius = None, setRemembered = False):
        from vision import VisionField
        return VisionField( self.tile,
                            lambda tile : tile.opaque(),
                            mark = None if not setRemembered else lambda tile : tile.remember()
        ).visible

class Item:
    def __init__(self, name, symbol, fgColour, bgColour = None):
        self.name = name
        self.symbol = symbol
        self.fgColour = fgColour
        self.bgColour = bgColour
    def appearance(self):
        rv = {
            'ch': self.symbol,
            'fg': self.fgColour
        }
        if self.bgColour:
            rv[ 'bg' ] = self.bgColour
        return rv

class Map:
    def __init__(self, context, width, height):
        self.x0, self.y0 = 0, 0
        self.context = context
        self.w, self.h = width, height
        self.tiles = {}
        for i in range(self.w):
            for j in range(self.h):
                self.tiles[i,j] = Tile(context,self, i,j)
        self.mobiles = []
        self.items = [] # NOTE: items on ground, not items kept in mobiles, containers or otherwise
        self.sim = timing.Simulator()
        self.previousLevel = None
        self.nextLevel = None
    def doRectangle(self, f, x0, y0, w, h):
        for x in range(x0, x0 + w):
            for y in range(y0, y0 + h):
                f( self.tiles[x,y] )
    def get(self, x, y):
        try:
            return self.tiles[x,y]
        except KeyError:
            return None
    def randomTile(self, criterion = lambda tile : True):
        import random
        choices = list( filter( criterion, self.tiles.values() ) )
        if not choices:
            return None
        return random.choice( choices )
    def spawnMobile(self, cls, *args, **kwargs):
        tile = self.randomTile( lambda tile : tile.spawnMonsters and not tile.mobile )
        assert tile != None
        rv = cls( tile, *args, **kwargs )
        return rv
    def spawnItem(self, cls, *args, **kwargs):
        tile = self.randomTile( lambda tile : tile.spawnItems )
        assert tile != None
        rv = cls( *args, **kwargs )
        tile.items.append( rv )
        return rv
    def getPlayerSpawnSpot(self, upwards = False):
        # around the stairs?
        origin = self.stairsDown if upwards else self.stairsUp
        from pathfind import Pathfinder, infinity
        import math
        pf = Pathfinder(cost = lambda tile : 1,
                        goal = lambda tile : not tile.impassable and not tile.mobile,
                        heuristic = lambda tile : 0,
        )
        pf.addOrigin( origin )
        path = pf.seek()
        return path[-1]

def mapFromGenerator( context ):
    lg = context.levelGenerator.get()
    rv = Map( context, lg.width, lg.height )
    # Ror now just the cell data is used; do recall that the lg object
    # also contains .rooms; these make up a graph that can be used to
    # classify the rooms.
    for x in range( lg.width ):
        for y in range( lg.height ):
            {
                ' ': makeImpenetrableRock,
                '+': lambda tile: makeOpenDoor(tile) if random.random() > 0.5 else makeClosedDoor(tile),
                'o': makeHallway,
                '.': makeFloor,
                '#': makeWall,
            }[ lg.data[y][x] ]( rv.tiles[x,y] )
    makeStairsUp( rv.tiles[ lg.entryRoom.internalFloorpoint() ] )
    makeStairsDown( rv.tiles[ lg.exitRoom.internalFloorpoint() ] )
    context.levels.append( rv )
    return rv

def innerRectangle( o, n = 0):
    return o.x0 + n, o.y0 + n, o.w - 2*n, o.h - 2*n

def mergeAppearance( result, target ):
    for key, val in target.items():
        result[ key ] = val

class Viewport:
    def __init__(self, level, window, visibility = lambda tile : True ):
        self.visibility = visibility
        self.window = window # set new on resize
        self.level = level
    def paint(self, cx, cy):
        x0 = cx - int(self.window.w / 2)
        y0 = cy - int(self.window.h / 2)
        for x in range(x0, x0 + self.window.w):
            for y in range(y0, y0 + self.window.h):
                try:
                    tile = self.level.tiles[x,y]
                except KeyError:
                    tile = None
                if tile and self.visibility( tile ):
                    outgoing = tile.appearance()
                elif tile and tile.remembered:
                    outgoing = tile.appearanceRemembered()
                else:
                    outgoing = { 'ch': ' ', 'fg': 'black', 'bg': 'black' }
                self.window.put( x - x0, y - y0, **outgoing )
