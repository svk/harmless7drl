import random
import sys

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
    def midpoint(self):
        return self.x0 + int(self.w/2), self.y0 + int(self.h/2)

class LevelGenerator:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.rooms = []
        self.hallwayLimit = 10 * (width + height)/2.0
        self.generate()
    def generateProtomap(self):
        self.data = []
        for y in range(self.height):
            self.data.append( [] )
            for x in range(self.width):
                wrote = False
                for rect in self.rooms:
                    if rect.contains( x, y ):
                        assert not wrote
                        self.data[-1].append( rect.data[y-rect.y0][x-rect.x0] )
                        wrote = True
                if not wrote:
                    self.data[-1].append( '-' )
    def generateRooms(self):
        rooms = self.rooms
        for rect in self.generateRectangles( 32, 44, 32, 44, 1, rooms ):
            rooms.append( Room( bigRoom = True, *rect.shrink(1).values() ) )
        for rect in self.generateRectangles( 12, 32, 12, 22, 1000, rooms ):
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
        self.rooms = rooms
        return self.rooms
    def generate(self):
        self.generateRooms()
        self.generateProtomap()
        self.markCorners()
        if not self.tryConnectAllNonvaults(tries=200):
            raise AgainException()
        self.makeSerendipitousDoors()
        self.makeEmptyDoorways(0.1)
        self.simplify()
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
    def tryConnect( self, alpha, beta ):
        if self.tryDigHallwayBetween( alpha, beta ):
            alpha.nowConnectedTo( beta )
            return True
        return False
    def tryConnectAllNonvaults(self, tries = 100):
        nonvaults = [room for room in self.rooms if not room.vault ]
        origin = random.choice( nonvaults )
        connected = set( [origin] )
        triesLeft = tries
        while len(connected) < len(nonvaults) and triesLeft > 0:
            self.tryConnectAny()
            newsies = []
            for room in connected:
                for connection in room.connections:
                    if connection not in connected:
                        newsies.append( connection )
            for newsie in newsies:
                connected.add( newsie )
            if newsies:
                triesLeft = tries
            else:
                tries -= 1
        return len(connected) == len(nonvaults)
    def getUnconnected( self, alpha ): # directly
        l = [ room for room in self.rooms if not room in alpha.connections and room != alpha and not room.vault ]
        if not l:
            return None
        return random.choice( l )
    def tryConnectToAny(self, alpha ):
        beta = self.getUnconnected( alpha )
        if not beta:
            return False
        return self.tryConnect( alpha, beta )
    def tryConnectAny(self):
        alpha = random.choice( [room for room in self.rooms if not room.vault] )
        return self.tryConnectToAny( alpha )
    def markCorners(self):
        for x in range(self.width):
            for y in range(self.height):
                if self.data[y][x] == '#':
                    fn = 0
                    for dx, dy in ((0,1),(0,-1),(1,0),(-1,0)):
                        fn += 1 if self.data[y+dy][x+dx] == '.' else 0
                    if fn == 0:
                        self.data[y][x] = 'C'
    def getRoomContaining(self, x, y):
        for room in self.rooms:
            if room.contains( x, y ):
                return room
    def makeSerendipitousDoorsForHallwayAt(self, x, y, probability = 1.0):
        hallway = set()
        unexplored = [ (x,y) ]
        neighbours = [ (0,1), (-1,0), (1,0), (0,-1) ]
        endpoints = []
        walls = {}
        while unexplored:
            x, y = unexplored.pop()
            if self.data[y][x] == '$':
                continue
            self.data[y][x] = '$'
            hallway.add( (x,y) )
            for dx, dy in neighbours:
                nx, ny = x+dx,y+dy
                if nx < 0 or ny < 0 or nx >= self.width or ny >= self.height:
                    continue
                if self.data[ny][nx] == '+':
                    room = self.getRoomContaining( nx, ny )
                    endpoints.append( room )
                if self.data[ny][nx] == ':':
                    unexplored.append( (nx,ny) )
                if self.data[ny][nx] in ['#', '[']:
                    dneigh, fneigh = 0, 0
                    for ddx, ddy in neighbours:
                        nnx, nny = nx+dx,ny+dy
                        if nnx < 0 or nny < 0 or nnx >= self.width or nny >= self.height:
                            continue
                        if self.data[nny][nnx] == '+':
                            dneigh += 1
                        if self.data[nny][nnx] == '.':
                            fneigh += 1
                    if dneigh > 0 or fneigh < 1:
                        continue
                    room = self.getRoomContaining( nx, ny )
                    try:
                        walls[ room ].append( (nx,ny) )
                    except KeyError:
                        walls[ room ] = [ (nx,ny) ]
        for key in walls:
            if key not in endpoints:
                if random.random() < probability:
                    x, y = random.choice( walls[key] )
                    self.data[y][x] = '+'
                    for end in endpoints:
                        end.nowConnectedTo( key )
                    endpoints.append( key )
    def makeSerendipitousDoors(self, probability = 1.0):
        did = True
        while did:
            did = False
            for y in range(self.height):
                for x in range(self.width):
                    if self.data[y][x] == ':':
                        self.makeSerendipitousDoorsForHallwayAt( x, y, probability )
                        did = True
                        break
                if did: break
    def makeEmptyDoorways(self, probability = 0.5):
        for x in range(self.width):
            for y in range(self.height):
                if self.data[y][x] == '+' and random.random() < probability:
                    self.data[y][x] = '.'
    def simplify(self):
        conversions = {
            '+': '+', # door
            '$': 'o', # procsesed hallway
            ':': 'o', # unprocsesed hallway
            '-': ' ', # impenetrable rock
            '=': ' ', # impenetrable rock (guard)
            '.': '.', # floor
            '#': '#', # wall
            '[': '#', # wall (guard)
            'C': '#', # wall (corner)
            '*': '#', # wall (internal border)
            '!': ' ', # impenetrable rock (internal non-border)
        }
        for x in range(self.width):
            for y in range(self.height):
                self.data[y][x] = conversions[ self.data[y][x] ]
    def tryDigHallwayBetween( self, alpha, beta):
        from pathfind import Pathfinder, infinity
        import math
        tx, ty = beta.floorpoint()
        ox, oy = alpha.floorpoint()
        assert self.data[oy][ox] == '.'
        assert self.data[ty][tx] == '.'
        costs = {
            '!': infinity,
            '*': infinity,
            '.': 1,
            '#': 100,
            '-': 10,
            ':': infinity,
            '+': infinity,
            'X': infinity,
            '=': infinity,
            'C': infinity,
            '[': infinity,
        }
        def cost( (x, y) ):
            if self.data[y][x] != '-':
                if not alpha.contains( x, y) and not beta.contains( x, y):
                    return infinity
            return costs[ self.data[y][x] ]
        pf = Pathfinder(cost = cost,
                        goal = lambda (x,y) : beta.contains(x, y) and self.data[y][x] == '.',
                        heuristic = lambda (x,y) : math.sqrt( (x-tx)*(x-tx) + (y-tx)*(y-tx) ),
                        neighbours = lambda (x,y) : [ (x+dx,y+dy) for (dx,dy) in ((0,1),(0,-1),(1,0),(-1,0)) if x+dx >= 0 and y+dy >= 0 and x+dx < self.width and y+dy < self.height ],
                        limit = self.hallwayLimit,
        )
        pf.addOrigin( (ox,oy) )
        path = pf.seek()
        if not path:
            return False
        protect = []
        for x, y in path:
            self.data[y][x] = {
                '#': '+',
                '-': ':',
                '.': '.',
                '=': ':',
                '[': ':',
            }[ self.data[y][x] ]
            if self.data[y][x] != '.':
                protect.append( (x,y) )
        for x, y in protect:
            for dx, dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
                try:
                    t = self.data[y+dy][x+dx]
                except IndexError:
                    continue
                if t == '#':
                    self.data[y+dy][x+dx] = '['
                if t == '-':
                    self.data[y+dy][x+dx] = '='
        return True

class Room (Rectangle):
    def __init__(self, x0, y0, w, h, bigRoom = False, vault = False):
        Rectangle.__init__(self, x0, y0, w, h)
        self.bigRoom = bigRoom
        self.vault = vault
        self.connections = set()
    def nowConnectedTo(self, that):
        self.connections.add( that )
        that.connections.add( self )
    def floorpoint(self):
        while True:
            x = random.randint( 0, self.w - 1)
            y = random.randint( 0, self.h - 1)
            if self.data[y][x] == '.':
                return x + self.x0,y + self.y0
    def createData(self):
        self.data = [ [ '.' for j in range(self.w) ] for i in range(self.h) ]
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
                    dot = '*'
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
                            dot = '*'
                self.data[y][x] = dot

class AgainException: pass

def generateLevel(width, height):
    while True:
        try:
            return LevelGenerator( width, height )
        except AgainException:
            print  >> sys.stderr, "warning: regenerating level -- should be unlikely"

import Queue
import threading
class GeneratorThread( threading.Thread ):
    def __init__(self, q):
        threading.Thread.__init__(self)
        self.q = q
        self.go = True
    def run(self):
        while self.go:
            lg = generateLevel( *self.args, **self.kwargs )
            self.q.put( lg )

class GeneratorQueue (Queue.Queue):
    def __init__(self, buffer, *args, **kwargs):
        Queue.Queue.__init__(self, buffer)
        self.thread = GeneratorThread( self )
        self.thread.args = args
        self.thread.kwargs = kwargs
        self.thread.start()
    def shutdown(self):
        self.thread.go = False
        self.get() # epic hack
        self.thread.join()

if __name__ == '__main__':
    import time
    generator = GeneratorThread( 2, 100, 100 )
    times = []
    print "Sleeping for 60 seconds to let the generator work.."
    time.sleep( 60 )
    t0 = time.time()
    while True:
        lg = None
        try:
            lg = generator.get( timeout = 1.0 )
        except Queue.Empty:
            print "Waiting for level..."
            continue
        dt = time.time() - t0
        t0 = time.time()
        for line in lg.data:
            print "".join( line )
        times.append( dt )
        print "Generated in", dt, "seconds"
        print "Average", sum(times) / float( len( times ) ), "seconds"
        print "Maximum", max(times), "seconds"
