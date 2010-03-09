# This module is definitely misnamed; in addition to level data it contains
# the Mobile class and the Item class, as well as the viewport that
# displays the map on screen.

# It does not and will not contain the level generator.

from timing import Speed

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
        self.level = level
        self.context = context
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
    def getRelative(self, dx, dy):
        return self.level.get( self.x + dx, self.y + dy )
    def neighbours(self):
        return [ self.getRelative(dx,dy) for dx in (-1,0,1) for dy in (-1,0,1) if dx or dy ]
    def describeHere(self):
        import grammar
        if self.items:
            ent = []
            ent.append( grammar.makeList( [ item.name for item in self.items ] ) )
            if len( self.items ) > 1:
                ent.append( "are" )
            else:
                ent.append( "is" )
            ent.append( "here." )
            self.context.log( grammar.capitalizeFirst( " ".join( ent ) ) )

def makeFloor( tile ):
    tile.name = "floor"
    tile.symbol = "."
    tile.impassable = False
    tile.spawnMonsters = True
    tile.spawnItems = True

def makeWall( tile ):
    tile.name = "wall"
    tile.symbol = "#"
    tile.impassable = True
    tile.spawnMonsters = False
    tile.spawnItems = False

class Mobile:
    def __init__(self, tile, name, symbol, speed = Speed.Normal, ai = None, context = None, fgColour = 'white', bgColour = None, noSchedule = False):
        self.name = name
        self.context = context
        self.symbol = symbol
        self.fgColour = fgColour
        self.bgColour = bgColour
        self.tile = None
        self.moveto( tile )
        self.speed = speed
        self.ai = ai
        self.sim = context.sim
        self.inventory = []
        self.noSchedule = noSchedule
        self.schedule()
    def moveto(self, tile):
        if self.tile:
            self.tile.leaves()
        assert not tile.cannotEnterBecause( self )
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
            self.sim.schedule( self, self.sim.t + self.speed )
    def trigger(self, t):
        if self.ai:
            self.ai.trigger( self )
        self.sim.schedule( self, t + self.speed )

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
                else:
                    outgoing = { 'ch': ' ', 'fg': 'magenta', 'bg': 'magenta' }
                self.window.put( x - x0, y - y0, **outgoing )
