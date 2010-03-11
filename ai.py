import random
import sys

def seekMob(mob, target, radius):
    from pathfind import Pathfinder, infinity
    import math
    pf = Pathfinder(cost = lambda tile : infinity if tile.cannotEnterBecause( mob ) and not tile.mobile == target  else 1,
                    goal = lambda tile : tile.mobile == target,
                    heuristic = lambda tile : max( abs( tile.x - target.tile.x ), abs( tile.y - target.tile.y ) ),
#                    tiebreaker = lambda tile : (tile.x - 5)**2 + (tile.y - 5)**2,
                    limit = radius,
    )
    pf.addOrigin( mob.tile )
    path = pf.seek()
    return path

def doRandomWalk( mob ):
    goodtiles = []
    for tile in mob.tile.neighbours():
        if not tile.cannotEnterBecause( mob ):
            goodtiles.append( tile )
    if goodtiles:
        tile = random.choice( goodtiles )
        mob.moveto( tile )


def doMeleeAlongPath( mob, target, path ):
    if path:
        if len( path ) > 2:
            tile = path[1]
            if not tile.cannotEnterBecause( mob ):
                mob.moveto( tile )
        elif len( path ) == 2:
            tile = path[1]
            if tile.mobile and tile.mobile == target and target.canBeMeleeAttackedBy( mob ):
                mob.meleeAttack( target )
        
def playerAccessibleForMelee(mob):
    return mob.context.player.canBeMeleeAttackedBy( mob )

def seekPlayer(mob, radius):
    return seekMob(mob, mob.context.player, radius)

def playerIsAdjacentTo(mob, tile):
    dx = mob.context.player.tile.x - tile.x
    dy = mob.context.player.tile.y - tile.y
    return max( abs(dx), abs(dy) ) == 1

def playerIsAdjacent(mob):
    return playerIsAdjacentTo(mob, mob.tile )

def doMeleePlayerOrFlee(mob):
    if playerAccessibleForMelee(mob):
        mob.meleeAttack( mob.context.player )
    else:
        goodtiles = []
        for tile in mob.tile.neighbours():
            if not tile.cannotEnterBecause( mob ) and not playerIsAdjacentTo( mob, tile ):
                goodtiles.append( tile )
        if goodtiles:
            tile = random.choice( goodtiles )
            mob.moveto( tile )
        

class RandomWalker:
    def trigger(self, mob):
        doRandomWalk( mob )

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
        

class MeleeSeeker:
    def __init__(self, radius):
        self.radius = radius
    def trigger(self, mob):
        if playerAccessibleForMelee( mob ):
            path = seekPlayer( mob, self.radius )
            if not path:
                doRandomWalk( mob )
            else:
                doMeleeAlongPath( mob, mob.context.player, path )
        else:
            doRandomWalk( mob )

class MeleeMagicHater:
    def __init__(self, radius, tolerance):
        self.radius = radius
        self.tolerance = tolerance
        self.enraged = False
    def playerPower(self, mob):
        if not mob.context.player.weapon:
            return 0
        return mob.context.player.weapon.mana
    def trigger(self, mob):
        if playerIsAdjacent( mob ):
            doMeleePlayerOrFlee( mob )
        else:
            path = seekPlayer( mob, self.radius )
            enraged = path and (self.playerPower(mob) > self.tolerance)
            if enraged and (not self.enraged):
                mob.logVisualMon( "%s stamps its feet!" )
                self.enraged = True
            elif enraged and self.enraged:
                doMeleeAlongPath( mob, mob.context.player, path )
            elif (not enraged) and self.enraged:
                mob.logVisualMon( "%s seems to calm down." )
                self.enraged = False
            else:
                doRandomWalk( mob )
