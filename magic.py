from level import Item, countItems, Rarity
from grammar import Noun, capitalizeFirst, makeCountingList
import grammar
import random
from widgets import *

ArcaneNames  = [ "Me", "Im", "Taz", "Ka", "Xe", "Mon", "Wil", "Vi", "Fon", "Bri", "Mos", "Han", "Osh", "Us", "Ik", "Mav", "Ex" ]
EnglishNames = { # -> rarity (level / inverse freq)
    "Move": Rarity( worth = 10, freq = 1 ),
    "Self": Rarity( worth = 10, freq = 1 ),
    "Negate": Rarity( worth = 10, freq = 1, minLevel = 2 ),
    "Destroy": Rarity( worth = 10, freq = 1, minLevel = 2 ),
    "Earth": Rarity( worth = 10, freq = 1),
    "Air": Rarity( worth = 10, freq = 1),
    "See": Rarity( worth = 10, freq = 1),
}

class Rune ( Item ):
    def __init__(self, arcaneName, englishName):
        Item.__init__(self,
                      self.generateNoun( arcaneName ),
                      '\\',
                      'magenta',
                      itemType = "rune",
                      weight = 1,
                      rarity = EnglishNames[ englishName ]
                      )
        self.arcaneName = arcaneName
        self.englishName = englishName
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
    def __init__(self, name, damage, minMana, maxMana, weight, rarity):
        Item.__init__(self, name, '|', 'yellow', itemType = "weapon", weight = weight, rarity = rarity)
        self.minMana, self.maxMana = minMana, maxMana
        self.magical = True
        self.damage = damage
    def stackname(self):
        return Noun( self.name.article,
                     self.name.singular + " (%d)" % self.mana,
                     self.name.plural + " (%d)" % self.mana,
                     self.name.gender,
                     self.name.the )
    def spawn(self):
        import copy
        rv = copy.copy( self )
        rv.mana = random.randint( self.minMana, self.maxMana )
        return rv

class TrapTalisman (Item):
    def __init__(self, name, weight, rarity):
        Item.__init__(self, name, '&', 'blue', itemType = "talisman", weight = weight, rarity = rarity )
        self.inventoryHooks.append( self )
    def onEnterInventory(self, mobile):
        mobile.trapDetection += 1
        if mobile.isPlayer():
            mobile.context.log( "You feel more perceptive." )
    def onLeaveInventory(self, mobile):
        mobile.trapDetection -= 1

class HealthTalisman (Item):
    def __init__(self, name, weight, rarity):
        Item.__init__(self, name, '&', 'red', itemType = "talisman", weight = weight, rarity = rarity )
        self.inventoryHooks.append( self )
    def onEnterInventory(self, mobile):
        mobile.maxHitpoints += 1
        if mobile.isPlayer():
            mobile.context.log( "You feel tougher." )
    def onLeaveInventory(self, mobile):
        mobile.maxHitpoints -= 1
        mobile.hitpoints = min( mobile.hitpoints, mobile.maxHitpoints )
        mobile.damage(0)

class Tome (Item):
    def __init__(self, name, rarity):
        Item.__init__(self,
                      name,
                      '?',
                      'white',
                      itemType = "tome",
                      weight = 10,
                      rarity = rarity)
    def identifyRune(self, context, inventory):
        unidentifiedRunes = list( filter( lambda rune : rune.itemType == "rune" and not rune.protorune.identified, inventory ) )
        unidentifiedRunes = set( list( map( lambda rune : rune.protorune, unidentifiedRunes ) ) )
        if not unidentifiedRunes:
            context.log( "The scroll can be used to reveal the nature of a single magical rune." )
            context.log( "You don't have any unidentified runes in your possession -- better save it for later." )
            return False
        rune = context.game.main.query( SelectionMenuWidget, choices = [
            (protorune, protorune.arcaneName) for protorune in unidentifiedRunes
        ] + [ (None, "cancel") ], title = "Identify which rune?", padding = 5 )
        if not rune:
            return False
        rune.identify()
        context.log( "You learn that \"%s\" means \"%s\"." % (rune.arcaneName, rune.englishName) )
        context.log( "The scroll disappears in a puff of smoke." )
        return True
        

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
                tile.enters( context.player ) # trigger? might not, flying etc.
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
                    if tile.mobile and tile.mobile.destroyedByDigging:
                        tile.mobile.killmessage()
                        tile.mobile.kill()
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

class LevitateSelf (Spell):
    def __init__(self):
        Spell.__init__( self, 'f', 'Flight', [ "Air", "Self" ] )
        self.buffName = "flight"
    def cost(self):
        return 10
    def cast(self, context):
        minduration, maxduration = 1000, 2000
        if context.player.flying:
            for key in context.player.buffs:
                if key.buffName == self.buffName:
                    context.player.buffs[ key ] += random.randint( minduration, maxduration )
            context.log( "You feel more confident in your ability to fly." )
        else:
            context.log( "Your feel lighter." )
            context.log( "You float into the air!" )
            context.player.flying = True
            context.player.buffs[ self ] = random.randint( minduration, maxduration )
    def debuff(self, context):
        context.player.flying = False
        context.log( "You feel heavier." )
        context.log( "You fall to the floor and land deftly on your feet." )
        context.player.tile.enters( context.player )
        del context.player.buffs[ self ]

class Invisibility (Spell):
    def __init__(self):
        Spell.__init__( self, 'i', 'Invisibility', [ "Negate", "See", "Self" ] )
        self.buffName = "invisibility"
    def cost(self):
        return 10
    def cast(self, context):
        minduration, maxduration = 400, 800
        if context.player.flying:
            for key in context.player.buffs:
                if key.buffName == self.buffName:
                    context.player.buffs[ key ] += random.randint( minduration, maxduration )
            context.log( "You feel less opaque." )
        else:
            context.log( "You disappear in a puff of smoke!" )
            context.log( "You are now invisible." )
            context.player.invisible = True
            context.player.buffs[ self ] = random.randint( minduration, maxduration )
    def debuff(self, context):
        context.player.invisible = False
        context.log( "Your limbs fade back into view." )
        context.log( "Your invisibility has worn off." )
        del context.player.buffs[ self ]

class MagicMap (Spell):
    def __init__(self):
        Spell.__init__( self, 'm', 'Reveal Map', [ "See", "Earth" ] )
    def cost(self):
        return 10
    def cast(self, context):
        for tile in context.player.tile.level.tiles.values():
            tile.remembered = True
        context.log( "You sense the shape of the dungeon around you." )

class Visions (Spell):
    def __init__(self):
        Spell.__init__( self, 'v', 'Visions', [ "Self", "See" ] )
        self.buffName = "visions"
    def cost(self):
        return 10
    def cast(self, context):
        minduration, maxduration = 400, 800
        if context.player.flying:
            for key in context.player.buffs:
                if key.buffName == self.buffName:
                    context.player.buffs[ key ] += random.randint( minduration, maxduration )
            context.log( "Your visions become more vivid." )
        else:
            context.log( "You begin to receive visions of your surroundings." )
            context.player.visions = True
            context.player.buffs[ self ] = random.randint( minduration, maxduration )
    def debuff(self, context):
        context.player.visions = False
        context.log( "Your visions subside." )
        del context.player.buffs[ self ]

Spells = [ TeleportSelf(), HealSelf(), Dig(), LevitateSelf(), Invisibility(), Visions(), MagicMap() ]

if __name__ == '__main__':
    counts = {}
    for rune in EnglishNames.keys():
        counts[rune] = 0
    for spell in Spells:
        for rune in spell.recipe:
            counts[rune] += 1
    rv = [ (count, rune) for rune,count in counts.items() ]
    rv.sort( reverse = True )
    for count, rune in rv:
        print rune, count
