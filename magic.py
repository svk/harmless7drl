from level import Item
from grammar import Noun
import random

ArcaneNames  = [ "Me", "Im", "Taz", "Ka", "Xe", "Mon", "Wil", "Vi", "Fon", "Bri", "Mos", "Han", "Osh", "Us", "Ik", "Mav", "Ex" ]
EnglishNames = { # -> rarity (level / inverse freq)
    "Move": 1,
    "Self": 1,
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
    def generateNoun(self, runename):
        return Noun( "a", "\"%s\" rune" % runename, "\"%s\" runes" % runename)
    def spawn(self):
        import copy
        return copy.copy( self )

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
        available = [ item.englishName for item in inventory if item.itemType == "rune" ]
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

Spells = [ TeleportSelf() ]
