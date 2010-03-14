# Warning - contains lots of spoilers

import random
import sys
from level import sign

def seekGoal(mob, target, radius, openDoors = False):
    from pathfind import Pathfinder, infinity
    import math
    pf = Pathfinder(cost = lambda tile : infinity if tile.cannotEnterBecause( mob ) and not target(tile) and not (openDoors and tile.name == "closed door") else 1,
                    goal = target,
                    heuristic = lambda tile : 0,
                    limit = radius,
    )
    pf.addOrigin( mob.tile )
    path = pf.seek()
    return path

def seekMob(mob, target, radius):
    from pathfind import Pathfinder, infinity
    import math
    pf = Pathfinder(cost = lambda tile : infinity if tile.cannotEnterBecause( mob ) and not tile.mobile == target  else 1,
                    goal = lambda tile : tile.mobile == target,
                    heuristic = lambda tile : max( abs( tile.x - target.tile.x ), abs( tile.y - target.tile.y ) ),
                    tiebreaker = lambda tile : (tile.x - target.tile.x)**2 + (tile.y - target.tile.y)**2,
                    limit = radius,
    )
    pf.addOrigin( mob.tile )
    path = pf.seek()
    return path

def doRandomWalk( mob, avoidTraps = True ):
    goodtiles = []
    for tile in mob.tile.neighbours():
        if not tile.cannotEnterBecause( mob ):
            if tile.trap and avoidTraps:
                continue
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
    if playerOutsideRadius( mob, radius ):
        return None
    return seekMob(mob, mob.context.player, radius)

def playerStepDistance(mob):
    return max( abs(mob.tile.x - mob.context.player.tile.x), abs(mob.tile.y - mob.context.player.tile.y ) )
    
def playerOutsideRadius(mob, radius): #optimization, basically
    return playerStepDistance( mob ) > radius

def playerIsAdjacentTo(mob, tile):
    dx = mob.context.player.tile.x - tile.x
    dy = mob.context.player.tile.y - tile.y
    return max( abs(dx), abs(dy) ) == 1

def playerIsAdjacent(mob):
    return playerIsAdjacentTo(mob, mob.tile )

def doFleePlayer( mob, openDoors = False ):
    # short-term flee "algo"
    goodtiles = []
    doortiles = []
    basic = mob.tile.distanceTo( mob.context.player.tile )
    for tile in mob.tile.neighbours():
        if not tile.cannotEnterBecause( mob ):
            d = tile.distanceTo( mob.context.player.tile )
            if d >= basic:
                goodtiles.append( (d, tile ) )
        elif openDoors and tile.isDoor and tile.doorState == "closed":
            doortiles.append( tile )
    if not goodtiles:
        from level import openDoor
        if doortiles:
            door = random.choice( doortiles )
            openDoor( door )
        return
    goodtiles.sort( reverse = True )
    goodtiles = list( filter( lambda (d,t) : d == goodtiles[0][0], goodtiles ) )
    d, tile = random.choice( goodtiles )
    mob.moveto( tile )

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
        
def doTrySpecialMeleePlayer(mob, radius, avoidTrapsRandomWalking = True):
    path = seekPlayer( mob, radius )
    if not path:
        doRandomWalk( mob, avoidTraps = avoidTrapsRandomWalking )
    else:
        target = mob.context.player
        if len( path ) > 2:
            tile = path[1]
            if not tile.cannotEnterBecause( mob ):
                mob.moveto( tile )
        elif len( path ) == 2:
            tile = path[1]
            if tile.mobile and tile.mobile == target and target.canBeMeleeAttackedBy( mob ):
                return True
    return False

class RandomWalker:
    def __init__(self, avoidTraps = True):
        self.avoidTraps = avoidTraps
    def trigger(self, mob):
        doRandomWalk( mob, avoidTraps = self.avoidTraps )

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
        if playerAccessibleForMelee( mob ) and not mob.context.player.invisible:
            path = seekPlayer( mob, self.radius )
            if not path:
                doRandomWalk( mob )
            else:
                doMeleeAlongPath( mob, mob.context.player, path )
        else:
            doRandomWalk( mob )

class IncorporealSeeker:
    # simply walk in the right dx, dy if you can
    # doesn't need to be used for an incorporeal mob, but it's
    #   a really stupid and robot-like way to move if not
    # rockform does not work against this monster -- it simply
    # waits right beside you
    def __init__(self):
        self.frustration = 0
    def trigger(self, mob):
        p = mob.context.player
        dx,dy = sign( p.tile.x - mob.tile.x ), sign( p.tile.y - mob.tile.y )
        tile = mob.tile.getRelative( dx, dy )
        if not tile:
            return # omgwtf
        if tile.mobile:
            if tile.mobile != p:
                self.frustration += 1
                if self.frustration > 5:
                    mob.logVisualMon( "%s touches " + tile.mobile.name.definiteSingular() + "." )
                    if not tile.mobile.essential:
                        tile.mobile.logVisualMon( "%s fades out of existence." )
                        tile.mobile.kill( noTriggerHooks = True )
                    else:
                        mob.logVisualMon( "%s stares at " + tile.mobile.name.definiteSingular() + " in surprise." )
                        mob.logVisualMon( "%s fades out of existence." )
                        mob.kill()
            elif playerAccessibleForMelee( mob ):
                mob.meleeAttack( p ) # for spectres, an instakill
        else:
            mob.logVisualMon( "%s floats slowly but steadily towards you." )
            mob.moveto( tile )
            self.frustration = 0

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
        if mob.context.player.invisible or not playerAccessibleForMelee( mob ):
            doRandomWalk( mob )
            return
        if playerIsAdjacent( mob ):
            doMeleePlayerOrFlee( mob )
        else:
            path = seekPlayer( mob, self.radius )
            if playerOutsideRadius(mob, self.radius):
                enraged = False
            else:
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

class Rook:
    def __init__(self, radius):
        self.radius = radius
    def trigger(self, mob):
        # the rook is entirely stationary unless it spots a clear
        # straight line to the player. If it does, moves 8 (radius)
        # tiles
        pl = mob.context.player
        if playerAccessibleForMelee( mob ):
            return
        if pl.invisible:
            return
        dx, dy = sign(pl.tile.x - mob.tile.x), sign(pl.tile.y - mob.tile.y)
        if dx != 0 and dy != 0:
            return # not a straight line, stationary
        tile = mob.tile.getRelative( dx, dy )
        dist = 0
        while not tile.mobile == pl:
            if not tile:
                return
            if tile.cannotEnterBecause( mob ):
                return
            dist += 1
            lastTile = tile
            tile = tile.getRelative( dx, dy )
        tile = lastTile
        # target acquired!
        if dist > self.radius:
            tile = mob.tile.getRelative( dx * self.radius, dy * self.radius )
            doAttack = False
        else:
            tile = pl.tile.getRelative( -dx, -dy )
            doAttack = True
        if not pl.canBeMeleeAttackedBy( mob ):
            doAttack = False
        aniTarget = pl.tile if doAttack else tile
        # show an animation, a ray from mob.tile to aniTarget
        raylen = max( abs(aniTarget.x - mob.tile.x), abs(aniTarget.y - mob.tile.y) )
        mob.context.game.showStraightRay( (mob.tile.x, mob.tile.y), (dx,dy), raylen, 'white', 'black' )
        mob.moveto( tile )
        if doAttack:
            mob.meleeAttack( pl )

class BoulderAi:
    def __init__(self, direction = (0,0), power = 2**30, speed = 16 ):
        self.direction = direction
        self.power = power
        self.speed = speed
    def inMotion(self):
        return self.direction != (0,0) and self.power > 0
    def trigger(self, mob):
        pass # pushing first, rolling comes later

class DebufferAi:
    def __init__(self, radius):
        self.radius = radius
        self.cooldown = 0
    def trigger(self, mob):
        # the debuffer can see invisible creatures.
        if self.cooldown > 0:
            self.cooldown -= 1
            doFleePlayer( mob )
        elif not playerAccessibleForMelee( mob ) or not mob.context.player.buffs:
            doFleePlayer( mob )
        else:
            path = seekPlayer( mob, self.radius )
            if not path:
                doRandomWalk( mob )
            else:
                target = mob.context.player
                if len( path ) > 2:
                    tile = path[1]
                    if not tile.cannotEnterBecause( mob ):
                        mob.moveto( tile )
                elif len( path ) == 2:
                    tile = path[1]
                    if tile.mobile and tile.mobile == target and target.canBeMeleeAttackedBy( mob ):
                        # instead of attacking..
                        mob.logVisualMon( "%s pricks you with a needle." )
                        buff = random.choice( target.buffs.keys() )
                        buff.debuff( target  )
                        self.cooldown = random.randint( 20, 40 )

class StaffStealer:
    def __init__(self, radius):
        self.radius = radius
        self.runmode = False
    def trigger(self, mob):
        if not self.runmode:
            if not playerAccessibleForMelee( mob ) or mob.context.player.invisible or not mob.context.player.weapon:
                doRandomWalk( mob, avoidTraps = True )
            else:
                if doTrySpecialMeleePlayer( mob, self.radius ):
                    mob.logVisualMon( "%s snatches your " + "%s!" % mob.context.player.weapon.name.singular )
                    mob.logVisualMon( "%s turns to run away!", usePronoun = 'subject' )
                    wep = mob.context.player.weapon
                    mob.context.player.weapon = None
                    mob.inventoryGive( wep )
                    self.runmode = True
        else:
            for tile in mob.tile.neighbours():
                if tile and tile.name == "stairs down":
                    below = tile.level.nextLevel.stairsUp
                    if not below.cannotEnterBecause( mob ):
                        mob.logVisualMon( "%s scuttles down the stairs." )
                        mob.moveto( below )
                        return
                if tile and tile.trap and tile.trap.trapname == "trapdoor":
                    below = tile.trap.getTarget()
                    if not below.cannotEnterBecause( mob ):
                        if mob.logVisualMon( "%s hops down a trapdoor!" ):
                            tile.trap.difficulty = 0
                        mob.moveto( below )
                        return
            path = seekGoal( mob, lambda tile : (tile.trap and tile.trap.trapname == "trapdoor") or (tile.name == "stairs down"), radius = 4 )
            if path and len(path) > 1:
                mob.moveto( path[1] )
            else:
                doFleePlayer( mob, openDoors = True )

class DigAnimal:
    def __init__(self, radius):
        self.radius = radius
        self.provoked = False
    def trigger(self, mob):
        # not affected by invisibility, since a mole navigates by smell (or what do I know, atleast not sight)
        if self.provoked and playerAccessibleForMelee( mob ):
            path = seekPlayer( mob, self.radius )
            if not path:
                self.randomDigWalk( mob )
            else:
                doMeleeAlongPath( mob, mob.context.player, path )
        else:
            self.randomDigWalk( mob )
    def randomDigWalk(self, mob ):
        digtiles = []
        goodtiles = []
        for tile in mob.tile.neighbours():
            if not tile.cannotEnterBecause( mob ):
                goodtiles.append( tile )
            elif tile.diggable() and tile.impassable:
                digtiles.append( tile )
        if digtiles and random.randint(0,1) > 0:
            from level import makeFloor
            digtile = random.choice( digtiles )
            mob.logVisualMon( "%s digs out a cave wall." )
            makeFloor( digtile )
            mob.moveto( digtile )
        elif goodtiles:
            tile = random.choice( goodtiles )
            mob.moveto( tile )

class ExplodesOnDeathHook:
    def __init__(self, radius, damage):
        self.radius = radius
        self.damage = damage
    def onDeath(self, mob):
        if not mob.logVisualMon( "%s explodes!" ):
            mob.logAural( "You hear an explosion." )
            # This is a hack -- should really be able to see only the parts of the explosion
            # in FOV. But hiding it entirely when the origin isn't in range looks better than
            # showing it all if any tile is in view.
            from level import disk
            region = disk( (mob.tile.x, mob.tile.y), self.radius )
        else:
            region = mob.context.game.showExplosion( (mob.tile.x, mob.tile.y), self.radius )
        affectlist = []
        for x, y in region:
            affects = mob.tile.level.tiles[x,y].mobile
            if affects and affects != mob and not affects.dead:
                affectlist.append( affects )
        for affects in affectlist:
            if affects:
                affects.logVisual( "You are caught in the blast!", "%s is caught in the blast!" )
                affects.damage( 1 )

class PlayerTrailFollower:
    # looks harmless, but will attack eventually if it stumbles on a trail
    # also rather easily led for this reason
    def __init__(self, radius):
        self.provoked = False
        self.radius = 5
    def trigger(self, mob):
        if self.provoked and playerAccessibleForMelee( mob ):
            path = seekPlayer( mob, self.radius )
            if not path:
                self.doTryTrail( mob )
            else:
                doMeleeAlongPath( mob, mob.context.player, path )
        else:
            self.doTryTrail( mob )
    def doTryTrail(self, mob):
        tile = mob.tile.playerTrail
        if not tile or tile.cannotEnterBecause( mob ):
            if tile and tile.mobile and tile.mobile.isPlayer() and tile.mobile.canBeMeleeAttackedBy( mob ):
                mob.meleeAttack( tile.mobile )
            else:
                doRandomWalk( mob )
        else:
            mob.moveto( tile )

class PursueWoundedAnimal:
    def __init__(self, radius):
        self.radius = radius
        self.enraged = False
        self.provoked = False
    def playerPower(self, mob):
        if not mob.context.player.weapon:
            return 0
        return mob.context.player.weapon.mana
    def trigger(self, mob):
        if not playerAccessibleForMelee( mob ):
            doRandomWalk( mob )
        path = None
        if mob.context.player.hitpoints < mob.context.player.maxHitpoints:
            path = seekPlayer( mob, self.radius )
        enraged = (self.provoked or path) and not mob.context.player.invisible
        if enraged and not self.enraged:
            if not mob.logVisualMon( "%s roars!" ):
                mob.logAural( "You hear a an animal roaring." )
        self.enraged = enraged
        if not self.enraged:
            if playerIsAdjacent( mob ):
                doMeleePlayerOrFlee( mob )
            else:
                doRandomWalk( mob )
        else:
            doMeleeAlongPath( mob, mob.context.player, path )

class ChokepointSleeperAnimal:
    def __init__(self, radius):
        self.radius = radius
        self.provoked = False
    def trigger(self, mob):
        if self.provoked and playerAccessibleForMelee( mob ) and not mob.context.player.invisible:
            path = seekPlayer( mob, self.radius )
            if not path:
                self.doChokepointSleeping( mob )
            else:
                doMeleeAlongPath( mob, mob.context.player, path )
        else:
            self.doChokepointSleeping( mob )
    def doChokepointSleeping(self, mob ):
        isChokepoint = lambda tile : (tile.mobile == mob or not tile.cannotEnterBecause(mob)) and len([n for n in tile.neighbours() if not n.impassable]) == 2
        if isChokepoint( mob.tile ):
            return
        path = seekGoal(mob, isChokepoint, self.radius, openDoors = True )
        if not path:
            doRandomWalk( mob )
        else:
            try:
                step = path[1]
            except IndexeError:
                return
            if step.isDoor:
                from level import makeFloor
                mob.logVisualMon( "%s knocks down the door." )
                makeFloor( step )
            else:
                mob.moveto( step )

class SpawnProtectorAnimal:
    def __init__(self, radius):
        self.radius = radius
        self.provoked = False
    def trigger(self, mob):
        if mob.childrenAttacked and not self.provoked:
            mob.logVisualMon( "%s bares its teeth!" )
            self.provoked = True
            for spawn in mob.children:
                spawn.ai.provoked = True
        if self.provoked and playerAccessibleForMelee( mob ) and not mob.context.player.invisible:
            path = seekPlayer( mob, self.radius )
            if not path:
                doRandomWalk( mob )
            else:
                doMeleeAlongPath( mob, mob.context.player, path )
        else:
            doRandomWalk( mob )

class SpawnAnimal:
    def __init__(self, radius):
        self.radius = radius
        self.provoked = False
    def trigger(self, mob):
        if self.provoked and playerAccessibleForMelee( mob ) and not mob.context.player.invisible:
            path = seekPlayer( mob, self.radius )
            if not path:
                self.wander( mob )
            else:
                doMeleeAlongPath( mob, mob.context.player, path )
        else:
            self.wander( mob )
    def wander(self, mob):
        maxdist = 8
        goodtiles = []
        halfwaytiles = []
        besttiles = []
        for tile in mob.tile.neighbours():
            if not tile.cannotEnterBecause( mob ):
                if tile.trap:
                    continue
                halfwaytiles.append( tile )
                if not tile.withinRadiusFrom( mob.protector.tile, 8):
                    continue
                goodtiles.append( tile )
                if not tile.withinRadiusFrom( mob.context.player.tile, 1.5 ):
                    continue
                besttiles.append( tile ) # they're curious.. and annoying
        tile = None
        if besttiles:
            tile = random.choice( besttiles )
        elif goodtiles:
            tile = random.choice( goodtiles )
        elif halfwaytiles:
            tile = random.choice( halfwaytiles )
        if tile:
            mob.moveto( tile )
