
class Tile:
    # Yes, keeping each tile in its own object, because I intend to do funky
    # stuff with the environment.
    def __init__(self, level, x, y):
        self.name = "null" # e.g. "floor", "wall"
        self.symbol = "?"
        self.fgColour = "white"
        self.bgColour = "black" # be careful setting this, need contrast
        self.impassable = True
        self.mobile = None
        self.level = level
        self.x, self.y = x, y
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
        if self.mobile:
            for key, val in self.mobile.appearance().items():
                rv[ key ] = val
        return rv
    def getRelative(self, dx, dy):
        return self.level.get( self.x + dx, self.y + dy )

def makeFloor( tile ):
    tile.name = "floor"
    tile.symbol = "."
    tile.impassable = False

def makeWall( tile ):
    tile.name = "wall"
    tile.symbol = "#"
    tile.impassable = True

class Mobile:
    def __init__(self, tile, name, symbol, fgColour = 'white'):
        self.name = name
        self.symbol = symbol
        self.fgColour = fgColour
        self.tile = None
        self.moveto( tile )
    def moveto(self, tile):
        if self.tile:
            self.tile.leaves()
        assert not tile.cannotEnterBecause( self )
        self.tile = tile
        self.tile.enters( self )
    def appearance(self):
        return {
            'ch': self.symbol,
            'fg': self.fgColour
        }

class Map:
    def __init__(self, width, height):
        self.x0, self.y0 = 0, 0
        self.w, self.h = width, height
        self.tiles = {}
        for i in range(self.w):
            for j in range(self.h):
                self.tiles[i,j] = Tile(self,i,j)
    def doRectangle(self, f, x0, y0, w, h):
        for x in range(x0, x0 + w):
            for y in range(y0, y0 + h):
                f( self.tiles[x,y] )
    def get(self, x, y):
        try:
            return self.tiles[x,y]
        except KeyError:
            return None

def innerRectangle( o, n = 0):
    return o.x0 + n, o.y0 + n, o.w - 2*n, o.h - 2*n

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
