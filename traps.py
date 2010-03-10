
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
    tile.trap = trap
    tile.onEnter.append( trap )

def installOpenDoorTrigger( tile, trap ):
    assert tile.isDoor
    assert tile.doorState == 'closed'
    tile.trap = trap
    tile.onOpen.append( trap )

class Trap:
    def __init__(self, difficulty):
        self.difficulty = random.randint(0, difficulty)
        self.active = True
    def canSpot(self, mob):
        return mob.trapDetection >= self.difficulty
    def __call__(self, mob):
        if self.active:
            mob.logVisual( "You trigger a generic trap!", "%s triggers a generic trap!" )
