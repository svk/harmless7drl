# Spiral FOV is my pet FOV algorithm. However, I always struggle
# with it for 7DRLs -- it's become a tradition. Let's see how I
# do this year. Starting 1847.

# Angles are measured such that 1.0 is one full circle. This is
# convenient to work with angles without many floating-point
# hassles.

from math import atan2, pi
import sys

def quadrant( x, y ):
    if x > 0:
        x = 1
    elif x < 0:
        x = -1
    if y > 0:
        y = 1
    elif y < 0:
        y = -1
    return x, y


def fromRadians( angle ):
    rv = angle / (2.0 * pi)
    return rv + 1 if rv < 0 else rv
        

def reduceAngle( angle ):
    rv = angle - int( angle )
    if rv < 0:
        rv += 1
    assert rv >= 0 and rv < 1
    return rv

class AngularInterval: #never full, sometimes empty
    def __init__(self, begin, end):
        self.begin = reduceAngle( begin )
        self.end = reduceAngle( end )
        self.crosses = self.begin > self.end
        self.empty = begin == end
    def contains(self, angle):
        if self.empty:
            return False
        if not self.crosses:
            return angle > self.begin and angle < self.end
        return angle > self.begin or angle < self.end
    def endIs(self, angle):
        if self.empty:
            return False
        return angle == self.end
    def intersect(self, that):
        # This is not a generally correct implementation of
        # intersection; sometimes the intersection of two intervals
        # is two disjoint sets -- this case is not handled.
        # It should never occur since we should never operate
        # with angles larger than pi.
        aye = False
        if self.contains( that.begin ):
            self.begin = that.begin
            aye = True
        if self.contains( that.end ):
            self.end = that.end
            aye = True
        if not aye:
            if not (that.contains( self.begin ) or that.contains( self.end )):
                self.empty = True
        return self
    def adjoin(self, that):
        # Check that this is safe instead of explicit left/right-adjoin.
        if self.end == that.begin:
            self.end = that.end
        if self.begin == that.end:
            self.begin = that.begin
        self.crosses = self.begin > self.end
        return self

class VisionField:
    def __init__(self, origin, obstacle, radius = None):
        self.origin = origin # a tile
        self.obstacle = obstacle
        if radius:
            self.radiusSquared = radius * radius
        else:
            self.radiusSquared = None
        self.q = []
        self.tiles = {}
        self.visible = set()
        self.visible.add( (origin.x, origin.y) )
        self.spiral = ( (1,0), (0,-1), (-1,0), (0,1) )
        self.passOrderings = {
            (1,0): ( (0,1), (1,0), (0,-1) ),
            (1,-1): ( (1,0), (0,-1) ),
            (0,-1): ( (1,0), (0,-1), (-1,0) ),
            (-1,-1): ( (0,-1), (-1,0) ),
            (-1,0): ( (0,-1), (-1,0), (0,1) ),
            (-1,1): ( (-1,0), (0,1) ),
            (0,1): ( (-1,0), (0,1), (1,0) ),
            (1,1): ( (0,1), (1,0) ),
        }
        initialAngles = [ 0.125, 0.375, 0.625, 0.825 ]
        for i in range(4):
            a0 = initialAngles[i-1]  #notice that this works with 0 and -1
            a1 = initialAngles[i]
            dx, dy = self.spiral[i]
            tile = origin.getRelative( dx, dy )
            if tile:
                self.addNew( tile, AngularInterval( a0, a1 ) )
        while self.q:
            self.calculate()
    def addNew(self, tile, aint):
        self.tiles[ tile.x, tile.y ] = aint
        self.q.append( tile )
    def calculate(self):
        next = self.q.pop(0)
        self.visible.add( (next.x, next.y) )
        rx, ry = next.x - self.origin.x, next.y - self.origin.y
        qxqy = quadrant( rx, ry )
        try:
            light = self.tiles[ next.x, next.y ]
        except KeyError:
            return # no light to pass
        del self.tiles[ next.x, next.y ]
        if self.radiusSquared and rx*rx + ry*ry > self.radiusSquared:
            return
        if self.obstacle( next ):
            qx, qy = qxqy
            ex, ey = qy, -qx
            if qx == 0:
                ey = -qy
            if qy == 0:
                ex = -qx
            maxa = fromRadians( atan2( -(2 * ry + ey), 2 * rx + ex ) )
            if light.endIs( maxa ):
                tile = next.getRelative( *self.passOrderings[qxqy][-1] )
                if tile:
                    self.q.append( tile )
            return
        for dx, dy in self.passOrderings[qxqy]:
            tile = next.getRelative( dx, dy )
            if not tile:
                continue
            assert (tile.x, tile.y) not in self.visible
            self.passLight( tile, light )
    def passLight(self, tile, lightIn):
        nrx, nry = tile.x - self.origin.x, tile.y - self.origin.y
        qx, qy = quadrant( nrx, nry )
        bx, by = -qy, qx
        ex, ey = qy, -qx
        if qx == 0:
            by, ey = -qy, -qy
        if qy == 0:
            bx, ex = -qx, -qx
        ba = fromRadians( atan2( -(2 * nry + by), 2 * nrx + bx ) )
        ea = fromRadians( atan2( -(2 * nry + ey), 2 * nrx + ex ) )
        light = AngularInterval( ba, ea ).intersect( lightIn )
        if light.empty:
            return
        try:
            self.tiles[ tile.x, tile.y ].adjoin( light )
        except KeyError:
            self.addNew( tile, light )
