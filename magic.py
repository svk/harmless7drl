from level import Item
from grammar import Noun
import random
from widgets import *

ArcaneNames  = [ "Me", "Im", "Taz", "Ka", "Xe", "Mon", "Wil", "Vi", "Fon", "Bri", "Mos", "Han", "Osh", "Us", "Ik", "Mav", "Ex" ]
EnglishNames = { # -> rarity (level / inverse freq)
    "Move": 1,
    "Self": 1,
    "Negate": 2,
    "Destroy": 1,
    "Earth": 1,
}

class Rune ( Item ):
    def __init__(self, arcaneName, englishName):
        Item.__init__(self,
                      self.generateNoun( arcaneName ),
                      '\\',
                      'magenta',
                      itemType = "rune",
                      )
        self.arcaneName = arcaneName
        self.englishName = englishName
        self.rarity = EnglishNames[ englishName ]
        self.identified = False
    def generateNoun(self, runename):
        return Noun( "an" if runename[0].upper() in "AEIOU" else "a", "\"%s\" rune" % runename, "\"%s\" runes" % runename)
    def spawn(self):
        import copy
        rv = copy.copy( self )
        rv.protorune = self
        return rv
    def identify(self): # use on the proto-runes
        newName = self.generateNoun( self.englishName )
        self.name.absorb( newName )
        self.identified = True


class Staff (Item):
    def __init__(self, name, damage, minMana, maxMana):
        Item.__init__(self, name, '|', 'yellow', itemType = "weapon")
        self.minMana, self.maxMana = minMana, maxMana
        self.magical = True
    def spawn(self):
        import copy
        rv = copy.copy( self )
        rv.mana = random.randint( self.minMana, self.maxMana )
        return rv

def generateProtorunes():
    assert len( EnglishNames ) <= len( ArcaneNames )
    random.shuffle( ArcaneNames )
    rv = []
    for arcane, english in zip( ArcaneNames, EnglishNames.keys() ):
        rv.append( Rune( arcane, english ) )
    return rv

class Spell:
    def __init__(self, hotkey, name, recipe):
        self.hotkey = hotkey
        self.name = name
        self.description = "%s (%s)" % (name, " ".join( recipe ) )
        self.recipe = set(recipe) # no repeated runes
    def canBuild(self, inventory):
        available = [ item.englishName for item in inventory if item.itemType == "rune" and item.protorune.identified ]
        for required in self.recipe:
            if required not in available:
                return False
        return True
    def build(self, inventory):
        if not self.canBuild( inventory ):
            return None
        for required in self.recipe:
            for i in range(len(inventory)):
                item = inventory[i]
                if item.itemType == "rune" and item.englishName == required:
                    break
            assert i < len(inventory)
            del inventory[i]
        return self

class TeleportSelf (Spell):
    def __init__(self):
        Spell.__init__( self, 'e', 'Escape', [ "Move", "Self" ] )
    def cost(self):
        return 5
    def cast(self, context):
        # teleport the player randomly. (greater teleport allows you to specify destination.)
        context.log( "You cast the Escape spell and teleport away!" )
        tile = context.player.tile.level.randomTile( lambda tile : not tile.trap and not tile.cannotEnterBecause( context.player ) )
        context.player.moveto( tile )

class Dig (Spell):
    def __init__(self):
        Spell.__init__( self, 'd', 'Dig', [ "Destroy", "Earth" ] )
    def cost(self):
        return 5
    def cast(self, context):
        # teleport the player randomly. (greater teleport allows you to specify destination.)
        context.log( "Dig in which direction?" )
        dx, dy = context.main.query( DirectionWidget )
        tile = context.player.tile.level.randomTile( lambda tile : not tile.trap and not tile.cannotEnterBecause( context.player ) )
        context.player.moveto( tile )

class Heal (Spell):
    def __init__(self):
        Spell.__init__( self, 'h', 'Heal', [ "Negate", "Destroy", "Self" ] )
    def cost(self):
        return 5
    def cast(self, context):
        # teleport the player randomly. (greater teleport allows you to specify destination.)
        context.log( "You feel invigorated." )
        context.player.hitpoints = context.player.maxHitpoints

Spells = [ TeleportSelf() ]
