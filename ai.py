import random
import sys

class RandomWalker:
    def trigger(self, mob):
        goodtiles = []
        for tile in mob.tile.neighbours():
            if not tile.cannotEnterBecause( mob ):
                goodtiles.append( tile )
        if goodtiles:
            tile = random.choice( goodtiles )
            mob.moveto( tile )

class HugBot:
    def __init__(self, target, radius):
        self.target = target
        self.radius = radius
    def trigger(self, mob):
        from pathfind import Pathfinder, infinity
        import math
        pf = Pathfinder(cost = lambda tile : infinity if tile.cannotEnterBecause( mob ) and not tile.mobile == self.target  else 1,
                        goal = lambda tile : tile.mobile == self.target,
                        heuristic = lambda tile : max( abs( tile.x - self.target.tile.x ), abs( tile.y - self.target.tile.y ) ),
                        limit = self.radius,
        )
        pf.addOrigin( mob.tile )
        path = pf.seek()
        if path and len( path ) > 1:
            tile = path[1]
            if not tile.cannotEnterBecause( mob ):
                mob.moveto( path[1] )

class TurnerBot:
    def __init__(self):
        self.directions = {
            (1,0): (0,1),
            (0,1): (-1,0),
            (-1,0): (0,-1),
            (0,-1): (1,0),
        }
        if random.randint(0,1):
            for key in self.directions:
                dx, dy = self.directions[key]
                self.directions[key] = -dx, -dy
        self.direction = random.choice( self.directions.keys() )
    def trigger(self, mob):
        
        tile = mob.tile.getRelative( *self.direction )
        if tile and not tile.cannotEnterBecause( mob ):
            mob.moveto( tile )
        else:
            self.direction = self.directions[ self.direction ]
            tile = mob.tile.getRelative( *self.direction )
            if tile and not tile.cannotEnterBecause( mob ):
                mob.moveto( tile )
        
