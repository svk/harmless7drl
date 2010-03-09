import random

class Rectangle:
    def __init__(self, x0, y0, w, h):
        self.x0, self.y0 = x0, y0
        self.w, self.h = w, h
    def area(self):
        return self.w * self.h
    def leastSide(self):
        return min( self.w, self.h )
    def intersect(self, that):
        x1, y1 = self.x0 + self.w - 1, self.y0 + self.h - 1 
        tx1, ty1 = that.x0 + that.w - 1, that.y0 + that.h - 1
        x0 = max( self.x0, that.x0 )
        y0 = max( self.y0, that.y0 )
        x1 = min( x1, tx1 )
        y1 = min( y1, ty1 )
        w = x1 - x0 + 1
        h = y1 - y0 + 1
        if w < 0 or h < 0:
            w = 0
            h = 0
        self.x0, self.y0, self.w, self.h = x0, y0, w, h
        return self
    def contains(self, x, y):
        return x >= self.x0 and x < self.x0 + self.w and y >= self.y0 and y < self.y0 + self.h
    def copy(self):
        return Rectangle(self.x0, self.y0, self.w, self.h)
    def shrink(self, n):
        self.x0 += n
        self.y0 += n
        self.w -= 2 * n
        self.h -= 2 * n
        assert self.w > 0 and self.h > 0
        return self
    def values(self):
        return self.x0, self.y0, self.w, self.h

class LevelGenerator:
    def __init__(self, width, height):
        self.width = width
        self.height = height
    def generateRectangles(self, minWidth, maxWidth, minHeight, maxHeight, tries, prevs = []):
        rv = []
        triesLeft = tries
        while triesLeft > 0:
            w = random.randint( minWidth, maxWidth )
            h = random.randint( minHeight, maxHeight )
            x = random.randint( 0, self.width - w )
            y = random.randint( 0, self.height - h )
            r = Rectangle( x, y, w, h )
            failed = False
            for rec in rv + prevs:
                if r.copy().intersect( rec ).area() > 0:
                    failed = True
                    break
            if failed:
                triesLeft -= 1
            else:
                triesLeft = tries
                rv.append( r )
        return rv

class Room (Rectangle):
    def __init__(self, x0, y0, w, h, bigRoom = False):
        Rectangle.__init__(self, x0, y0, w, h)
        self.bigRoom = bigRoom
    def createData(self):
        self.data = [ [ '.' for j in range(w) ] for i in range(h) ]
    def makeRectangular(self):
        for x in range( self.w ):
            for y in range( self.h ):
                if x == 0 or y == 0 or x+1 == self.w or y+1 == self.h:
                    dot = '#'
                else:
                    dot = '.'
                self.data[y][x] = dot
    def makeRectangularCornerclipped(self, minimal = 1):
        srw = random.randint( minimal, int(self.w/2) )
        srh = random.randint( minimal, int(self.h/2) )
        srx = self.w - srw if random.randint(0,1) else 0
        sry = self.h - srh if random.randint(0,1) else 0
        subrect = Rectangle( srx, sry, srw, srh )
        nbs = [ (0,1), (1,0), (-1,0), (0,-1) ] + [ (1,1), (1,-1), (-1,1), (-1,-1) ]
        def inside(a,b):
            return a >= 0 and b >= 0 and a < self.w and b < self.h and not subrect.contains( a, b )
        for x in range( self.w ):
            for y in range( self.h ):
                dot = '.'
                if not inside(x,y):
                    dot = '-'
                else:
                    for dx, dy in nbs:
                        if not inside(x+dx,y+dy):
                            dot = '#'
                self.data[y][x] = dot
    def makeCavernous(self):
        tiles = {}
        for x in range( self.w ):
            for y in range( self.h ):
                hubness = min( x, self.w - x - 1, y, self.h - y - 1)
                edginess = max( self.w, self.h ) - hubness if hubness > 0 else 2**31 #hax
                tiles[x,y] = edginess
        cset = []
        oset = [ (int(self.w/2), int(self.h/2)) ]
        tiles[ oset[0] ] = 0
        nbs = [ (0,1), (1,0), (-1,0), (0,-1) ]
        dnbs = [ (1,1), (1,-1), (-1,1), (-1,-1) ]
        while len( oset + cset ) < self.area() * 0.6:
            x, y = next = random.choice( oset )
            bs = []
            for dx, dy in nbs:
                try:
                    nb = tiles[x+dx,y+dy]
                    if nb <= 0: continue
                    bs.append( (x+dx,y+dy) )
                except KeyError:
                    continue
            if not bs:
                oset.remove( next )
                cset.append( next )
                continue
            else:
                x, y = random.choice( bs )
                tiles[x,y] -= 1
                if tiles[x,y] <= 0:
                    oset.append( (x,y) )
        digged = set( cset + oset )
        for x in range( self.w ):
            for y in range( self.h ):
                dot = '-'
                if (x,y) in digged:
                    dot = '.'
                else:
                    for dx, dy in nbs+dnbs:
                        if (x+dx,y+dy) in digged:
                            dot = '#'
                self.data[y][x] = dot
    def generateFloorRect(self, minWidth, minHeight, tries = 100):
        while tries > 0:
            w = random.randint( minWidth, self.w )
            h = random.randint( minHeight, self.h )
            x = random.randint( 0, self.w - w )
            y = random.randint( 0, self.h - h )
            fail = False
            for i in range(w):
                for j in range(h):
                    if self.data[y+j][x+i] != '.':
                        fail = True
            if not fail:
                return Rectangle( x, y, w, h )
            tries -= 1
        return None
    def fillSubrectangleRectangular(self, rect):
        for x in range(rect.x0, rect.x0 + rect.w):
            for y in range(rect.y0, rect.y0 + rect.h):
                assert self.data[y][x] == '.'
                if x == rect.x0 or y == rect.y0 or x + 1 == rect.x0 + rect.w or y + 1 == rect.y0 + rect.h:
                    dot = '#'
                else:
                    dot = '!'
                self.data[y][x] = dot
    def fillSubrectangleRounded(self, rect):
        filled = []
        for x in range(rect.x0, rect.x0 + rect.w):
            for y in range(rect.y0, rect.y0 + rect.h):
                filled.append( (x,y) )
        nbs = [ (0,1), (1,0), (-1,0), (0,-1) ] + [ (1,1), (1,-1), (-1,1), (-1,-1) ]
        def inside(a,b):
            return rect.contains(a,b) and (a,b) in filled
        for i in range( len( filled ) / 4 ):
            hasNbNin = False
            x, y = random.choice( filled )
            for dx, dy in nbs:
                if not inside( x+dx, y+dy ):
                    hasNbNin = True
            if hasNbNin:
                filled.remove( (x,y) )
        for x in range(rect.x0, rect.x0 + rect.w):
            for y in range(rect.y0, rect.y0 + rect.h):
                dot = '.'
                if inside(x,y):
                    dot = '!'
                    for dx, dy in nbs:
                        if not inside(x+dx,y+dy):
                            dot = '#'
                self.data[y][x] = dot

if __name__ == '__main__':
    import sys
    r1 = Rectangle( 0, 0, 40, 25 )
    r2 = Rectangle( 20, 10, 10, 10 )
    r1.intersect( r2 )
    w, h = 100, 100
    lg = LevelGenerator( w, h )
    rooms = []
    for rect in lg.generateRectangles( 32, 44, 32, 44, 1, rooms ):
        rooms.append( Room( bigRoom = True, *rect.shrink(1).values() ) )
    for rect in lg.generateRectangles( 12, 32, 12, 22, 1000, rooms ):
        rooms.append( Room( *rect.shrink(1).values() ) )
    for room in rooms:
        room.createData()
        rounded = False
        if room.leastSide() > 16:
            room.makeCavernous()
            rounded = True
        elif random.randint(0,1):
            room.makeRectangularCornerclipped( minimal = 3)
        else:
            room.makeRectangular()
        if random.randint(0,1):
            dist = 2
            subrect = room.generateFloorRect( 5 + dist*2, 5 + dist*2 )
            if subrect:
                if rounded:
                    room.fillSubrectangleRounded( subrect.shrink(dist - 1) )
                else:
                    room.fillSubrectangleRectangular( subrect.shrink(dist) )
    print len( rooms )
    for y in range(h):
        for x in range(w):
            wrote = False
            for rect in rooms:
                if rect.contains( x, y ):
                    assert not wrote
                    sys.stdout.write( rect.data[y-rect.y0][x-rect.x0] )
                    wrote = True
            if not wrote:
                sys.stdout.write( '-' )
        sys.stdout.write( '\n' )
