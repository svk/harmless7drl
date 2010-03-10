
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

import random


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
    def __init__(self, context, difficulty):
        self.difficulty = random.randint(0, difficulty)
        self.context = context
        self.active = True
        self.tiles = []
        self.lists = []
    def canSpot(self, mob):
        return mob.trapDetection >= self.difficulty
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
    def __init__(self, tile, *args, **kwargs):
        Trap.__init__(self, difficulty = 0, *args, **kwargs)
        installStepTrigger( tile, self )
    def __call__(self, mob):
        mob.logVisual( "You fall into the spike pit!", "%s falls into the spike pit!" )
        mob.killmessage()
        mob.kill()

class ExplodingMine (Trap):
    def __init__(self, tile, *args, **kwargs):
        Trap.__init__(self, difficulty = 0, *args, **kwargs)
        self.blastSize = 5
        installStepTrigger( tile, self )
    def __call__(self, mob):
        if not mob.logVisual( "You set off a mine!", "%s sets off a mine!" ):
            mob.logAural( "You hear an explosion." )
        for x, y in self.context.game.showExplosion( (mob.tile.x, mob.tile.y), self.blastSize ):
            affects = mob.tile.level.tiles[x,y].mobile
            if affects:
                affects.logVisual( "You are caught in the explosion!", "%s is caught in the explosion!" )
                affects.damage( 1 )
        self.remove()
