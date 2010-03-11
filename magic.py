from level import Item, countItems
from grammar import Noun, capitalizeFirst, makeCountingList
import grammar
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
        self.damage = damage
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
        from level import makeFloor
        from traps import TrapDoor, clearTraps
        context.log( "Dig in which direction?" )
        dxdy = context.game.main.query( DirectionWidget, acceptZ = True )
        nodig = [ "stairs up", "stairs down" ]
        if dxdy == '<':
            tile = context.player.tile
            prevLev = tile.level.previousLevel
            if not prevLev:
                context.log( "You fail to dig through the ceiling." )
            else:
                tileAbove = prevLev.randomTile( lambda tile : not tile.impassable and not tile.trap and not tile.mobile and not tile.name in nodig )
                td = TrapDoor( tileAbove, context = context )
                td.difficulty = 0
                td.setTarget( tile )
                context.log( "You dig through the ceiling!" )
                items = tileAbove.items
                tileAbove.items = []
                if items:
                    tile.level.scatterItemsAround( items, (tile.x, tile.y) )
                    msg = [ capitalizeFirst( grammar.makeCountingList( countItems( items ) ) ),
                            "fall" if len(items) > 1 else "falls",
                            "through the hole!" ]
                    context.log( " ".join( msg ) )
        elif dxdy == '>':
            tile = context.player.tile
            nexLev = tile.level.generateDeeperLevel()
            if nexLev and tile.name not in nodig:
                clearTraps( tile )
                td = TrapDoor( tile, context = context )
                td.difficulty = 0
                items = tile.items
                tile.items = []
                target = td.getTarget()
                context.log( "You dig through the floor!" )
                if items:
                    tile.level.scatterItemsAround( items, target )
                    msg = [ capitalizeFirst( grammar.makeCountingList( countItems( items ) ) ),
                            "fall" if len(items) > 1 else "falls",
                            "through the hole!" ]
                    context.log( " ".join( msg ) )
                tile.enters( context.player )
            else:
                context.log( "You fail to dig through the floor." )
        else:
            rayLength = 8
            region = context.game.showStraightRay( (context.player.tile.x,context.player.tile.y),
                                                   dxdy,
                                                   rayLength,
                                                   'black',
                                                   'magenta',
                                                   lambda (x,y) : not context.player.tile.level.tiles[x,y].diggable()
            )
            for x, y in region:
                try:
                    tile = context.player.tile.level.tiles[x,y]
                    if tile.diggable() and tile.impassable:
                        makeFloor( tile )
                except KeyError: # shouldn't happen
                    break

class HealSelf (Spell):
    def __init__(self):
        Spell.__init__( self, 'h', 'Heal', [ "Negate", "Destroy", "Self" ] )
    def cost(self):
        return 5
    def cast(self, context):
        # teleport the player randomly. (greater teleport allows you to specify destination.)
        context.log( "You feel invigorated." )
        context.player.hitpoints = context.player.maxHitpoints

Spells = [ TeleportSelf(), HealSelf(), Dig() ]
