
# known triggers:
#       - entering a tile (this is the big one; also goes for
#         prox traps, just link several tiles)
#       - opening a door
#       - opening a chest
#       - picking up an item

# The trap may or may not choose to deactivate itself after
# triggering. A spike pit would never deactivate, while a
# boulder trap would deactivate after one


# detected traps (triggers) are displayed in red (?)
# -- the _background_ colour.

# trap detection difficulty: the trap rolls _once_, for
# difficulty -- your detection ability is static except for
# character improvement [and there is never a reason to
# decrease your trap detection ability, e.g. it does not
# share a slot] -- this is to avoid encouraging tedious
# trap-detecting activities.
# Some traps are "obvious", having difficulty 0; any
# character can spot these

import sys
import random
from level import Rarity

def clearTraps( tile ):
    tile.trap = None
    tile.onEnter = [] #XXX if any other hooks are added
    tile.onOpen = []

def installStepTrigger( tile, trap ):
    trap.tiles.append( tile )
    trap.lists.append( tile.onEnter )
    tile.trap = trap
    tile.onEnter.append( trap )

def installOpenDoorTrigger( tile, trap ):
    assert tile.isDoor
    assert tile.doorState == 'closed'
    trap.tiles.append( tile )
    trap.lists.append( tile.onOpen )
    tile.trap = trap
    tile.onOpen.append( trap )

class Trap:
    def __init__(self, context, difficulty, fillable = False):
        self.difficulty = random.randint(0, difficulty)
        self.context = context
        self.active = True
        self.tiles = []
        self.lists = []
        self.trapname = None
        self.fillable = fillable
    def canSpot(self, mob):
        return mob.trapDetection >= self.difficulty
    def describe(self):
        return "A trap."
    def remove(self):
        for tile in self.tiles:
            assert tile.trap == self
            tile.trap = None
        for triggerlist in self.lists:
            triggerlist.remove( self )
    def __call__(self, mob):
        if self.active:
            mob.logVisual( "You trigger a generic trap!", "%s triggers a generic trap!" )

class SpikePit (Trap):
    # since this one is always visible, it is mostly a help
    # rather than a hindrance to players -- they can trick monsters
    # into it.
    rarity = Rarity( freq = 1 )
    def __init__(self, tile, *args, **kwargs):
        Trap.__init__(self, difficulty = 0, fillable = True, *args, **kwargs)
        installStepTrigger( tile, self )
    def __call__(self, mob):
        mob.logVisual( "You fall into the spike pit!", "%s falls into the spike pit!" )
        mob.killmessage()
        mob.kill()
    def describe(self):
        return "A spike pit."

class ExplodingMine (Trap):
    rarity = Rarity( freq = 1, minLevel = 3 )
    def __init__(self, tile, *args, **kwargs):
        Trap.__init__(self, difficulty = 2, *args, **kwargs)
        self.blastSize = 5
        self.power = 3
        installStepTrigger( tile, self )
    def __call__(self, mob):
        if not mob.logVisual( "You set off a mine!", "%s sets off a mine!" ):
            mob.logAural( "You hear an explosion." )
        for x, y in self.context.game.showExplosion( (mob.tile.x, mob.tile.y), self.blastSize ):
            affects = mob.tile.level.tiles[x,y].mobile
            if affects:
                affects.logVisual( "You are caught in the explosion!", "%s is caught in the explosion!" )
                affects.damage( self.power )
        self.remove()
    def describe(self):
        return "A mine."

class TrapDoor (Trap):
    rarity = Rarity( freq = 1, minLevel = 2 )
    def __init__(self, tile, *args, **kwargs):
        Trap.__init__(self, difficulty = 4, *args, **kwargs)
        self.blastSize = 5
        installStepTrigger( tile, self )
        self.target = None
        self.trapname = "trapdoor"
    def describe(self):
        if self.difficulty > 0:
            return "A trap door."
        return "A hole in the floor."
    def __call__(self, mob):
        mob.logVisual( "You fall through a hole in the floor!", "%s falls down a hole in the floor!" )
        self.getTarget()
        tile = self.target.level.getClearTileAround( self.target, lambda tile : not tile.impassable and not tile.mobile )
        mob.moveto( tile )
        mob.damage( 1 )
        self.difficulty = 0
    def getTarget(self):
        if not self.target:
            if not self.tiles[0].level.nextLevel:
                self.tiles[0].level.generateDeeperLevel()
            tile = self.tiles[0].level.nextLevel.randomTile( lambda tile : not tile.impassable )
            self.setTarget( tile )
        return self.target
    def setTarget(self, tile):
        self.target = tile
        self.target.ceilingHole = self.tiles[0]

class CannotPlaceTrap:
    pass

class ArrowTrap (Trap):
    rarity = Rarity( freq = 1 )
    def __init__(self, tile, *args, **kwargs):
        directions = {
            'west': (-1,0),
            'east': (1,0),
            'north': (0,-1),
            'south': (0,1),
        }
        self.directionName = random.choice( directions.keys() )
        next = tile
        while next and not next.impassable:
            next = next.getRelative( *directions[self.directionName] )
        if not next or next.arrowSlit or next.name != "wall":
            raise CannotPlaceTrap()
        self.arrowOrigin = next
        dx, dy = directions[self.directionName]
        self.arrowDirection = -dx,-dy
        Trap.__init__(self, difficulty = 4, *args, **kwargs)
        self.blastSize = 5
        installStepTrigger( tile, self )
        self.target = None
        self.trapname = "arrowtrap"
        self.ammo = random.randint(1,10)
        self.power = 1
        self.arrowOrigin.arrowSlit = True
    def describe(self):
        return "An arrow trap."
        return "A dart trap (arrow slit to the %s)." % self.directionName
    def __call__(self, mob):
        didHear = mob.logVisual( "You trigger a trap!", "%s triggers a trap!" )
        if didHear:
            self.difficulty = 0
        if self.ammo < 1:
            if didHear:
                mob.context.log( "You hear a click from a mechanism in a nearby wall." )
            return
        self.ammo -= 1
        tile = self.arrowOrigin
        hit = mob.context.game.showStraightRay( (self.arrowOrigin.x, self.arrowOrigin.y),
                                     self.arrowDirection,
                                     2**31,
                                     'yellow',
                                     'black', 
                                     stopper = lambda k : not tile.level.tiles.has_key( k ) or tile.level.tiles[k].impassable or tile.level.tiles[k].mobile,
                                     projectile = True,
        )
        try:
            hit = hit[0]
            arrowHit = mob.tile.level.tiles[hit].mobile
            arrowHit.tile
        except (IndexError,KeyError, AttributeError):
            return # not sure that this is possible
        arrowHit.logVisual( "You're struck by an arrow!", "%s is struck by an arrow!" )
        arrowHit.damage( self.power )

class TeleportationTrap (Trap):
    rarity = Rarity( freq = 100, maxLevel = 5 )
    def __init__(self, tile, *args, **kwargs):
        Trap.__init__(self, difficulty = 10, *args, **kwargs)
        installStepTrigger( tile, self )
        self.target = None
        self.trapname = "teletrap"
    def describe(self):
        return "A teleportation trap."
    def __call__(self, mob):
        if mob.isPlayer():
            self.difficulty = 0
        mob.logVisual( "Your surroundings suddenly shift!", "%s disappears!" )
        self.getTarget()
        tile = self.target.level.getClearTileAround( self.target, lambda tile : not tile.impassable and not tile.mobile )
        mob.moveto( tile )
        if not mob.isPlayer():
            mob.logVisualMon( "%s reappears!" )
    def getTarget(self):
        if not self.target:
            tile = self.tiles[0].level.randomTile( lambda tile : not tile.impassable )
            self.setTarget( tile )
        return self.target
    def setTarget(self, tile):
        self.target = tile

Traps = [ SpikePit, ExplodingMine, ArrowTrap, TrapDoor, TeleportationTrap ]
        
        
# 21:20
        
