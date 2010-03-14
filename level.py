# This module is definitely misnamed; in addition to level data it contains
# the Mobile class and the Item class, as well as the viewport that
# displays the map on screen.

# It does not and will not contain the level generator.

import sys
import random
from timing import Speed
import timing
from grammar import *
from widgets import SelectionMenuWidget

DungeonDepth = 2 # the dungeon is infinite, but the macguffin will be at this
                 # level and there will be no further variety in monsters/items etc.

class Rarity:
    def __init__(self, worth = 1, freq = 1, minLevel = -2**31, maxLevel = 2**31):
        self.worth = 1
        self.frequency = freq
        self.minLevel = minLevel
        self.maxLevel = maxLevel
    def eligible(self, dlevel):
        return dlevel >= self.minLevel and dlevel <= self.maxLevel

from traps import *

def weightedSelect( things ):
    totalWeight = sum( map( lambda thing : thing.rarity.frequency, things ) )
    try:
        selected = random.randint( 0, totalWeight - 1 )
    except ValueError:
        return None
    for thing in things:
        selected -= thing.rarity.frequency
        if selected < 0:
            return thing
    return None

def selectThings( dlevel, target, things ):
    rv = []
    while target > 0:
        thing = weightedSelect( [ thing for thing in things if thing.rarity.eligible( dlevel ) ] )
        if not thing:
            break
        rv.append( thing )
        target -= thing.rarity.worth
    # note: this still returns PROTO-things, which must be handled
    # as appropriately (e.g. .spawn() for items)
    return rv

class PlayerWonException:
    pass

class PlayerKilledException:
    def __init__(self, didQuit = False):
        self.didQuit = didQuit

def countItems( l ):
    rv = {}
    for item in l:
        try:
            rv[item.stackname()].append( item )
        except KeyError:
            rv[item.stackname()] = [item]
    return rv

def generateTrapsForRoom( rv, context, room ):
    # simple sample trap
    from traps import Traps, CannotPlaceTrap
    for trap in selectThings( rv.depth, random.randint(2,5), Traps ):
        tries = 100
        while tries > 0:
            point = rv.tiles[ room.internalFloorpoint() ]
            if not point.trap:
                break
            tries -= 1
        if tries > 0:
            try:
                singleCell = trap
                trap = singleCell( point, context = context )
            except CannotPlaceTrap:
                pass
    if rv.depth > 5 and random.random() < 0.25:
        for x, y in room.coordinates(): # XXX don't always have the exit room turbulent
            try:
                tile = rv.tiles[x,y]
            except KeyError:
                continue
            tile.createTurbulence()

class Tile:
    # Yes, keeping each tile in its own object, because I intend to do funky
    # stuff with the environment.
    def __init__(self, context, level, x, y):
        self.name = "null" # e.g. "floor", "wall"
        self.symbol = "?"
        self.fgColour = "white"
        self.bgColour = "black" # be careful setting this, need contrast
        self.impassable = True
        self.mobile = None
        self.spawnItems = False
        self.spawnMonsters = False
        self.hindersLOS = True
        self.level = level
        self.isDoor = False
        self.context = context
        self.x, self.y = x, y
        self.items = []
        self.trap = None
        self.onEnter = []
        self.onOpen = []
        self.tileTypeDesc = "A NULL tile."
        self.isBorder = False
        self.ceilingHole = None
        self.groundTile = True
        self.playerTrail = None
        self.isPortal = False
        self.turbulenceRedirect = None
        self.arrowSlit = False
        self.rememberedAs = None
    def isTurbulent(self):
        return self.turbulenceRedirect != None
    def createTurbulence(self):
        try:
            self.turbulenceRedirect = random.choice( [ n for n in self.neighbours() if not n.impassable ] )
        except IndexError:
            self.turbulenceRedirect = random.choice( [ n for n in self.neighbours() ] )
    def calmTurbulence(self):
        self.turbulenceRedirect = None
        for n in self.neighbours():
            if n.turbulenceRedirect:
                n.calmTurbulence()
    def cannotEnterBecause(self, mobile):
        # may be called with a protomonster!
        if self.mobile != None:
            return "there's something in the way"
        if mobile.incorporeal and not self.isBorder:
            return ""
        if self.groundTile and not mobile.walking:
            return "you can't walk on solid ground"
        if self.impassable:
            return "tile is impassable"
        return ""
    def leaves(self):
        self.mobile = None
    def describe(self):
        rv = []
        if self.tileTypeDesc:
            rv.append( self.tileTypeDesc )
        if self.mobile:
            rv.append( self.mobile.describe() )
        if self.trap and self.trap.canSpot( self.context.player ):
            rv.append( self.trap.describe() )
        if self.arrowSlit:
            rv.append( "An arrow slit." )
        if self.ceilingHole:
            rv.append( "A hole in the ceiling." )
        if self.items:
            rv.append( self.describeItems() + "." )
        return " ".join( rv )
    def distanceTo(self, that):
        import math
        return math.sqrt( self.distanceToSquared( that ) )
    def distanceToSquared(self, that):
        return (self.x-that.x)*(self.x-that.x) + (self.y-that.y)*(self.y-that.y)
    def withinRadiusFrom(self, origin, radius):
        return self.distanceToSquared( origin ) <= radius * radius
    def describeRemembered(self):
        return self.rememberedAs.tileTypeDesc
    def enters(self, mobile, turbulenceProbability = 1.0):
        if mobile.isBoulder and self.trap and self.trap.fillable:
            self.trap.remove()
            mobile.kill()
            return
        self.mobile = mobile
        if not mobile.flying:
            for trigger in self.onEnter: # XXX should be called onStep
                trigger( mobile )
        if self.turbulenceRedirect and mobile.isPlayer():
            if random.random() < 0.75 and not mobile.flying:
                self.context.log( "You resist a gust of unnatural wind!" )
            elif random.random() < turbulenceProbability and not self.turbulenceRedirect.cannotEnterBecause( mobile ):
                if turbulenceProbability == 1.0:
                    self.context.log( "You are blown away by a gust of magical wind!" )
                mobile.moveto( self.turbulenceRedirect, turbulenceProbability = turbulenceProbability / 2.0, neverfail = True )
    def appearance(self):
        rv = {
            'ch': self.symbol,
            'fg': self.fgColour,
            'bg': self.bgColour,
        }
        if self.items:
            mergeAppearance( rv, self.items[-1].appearance() )
        if self.mobile:
            if not self.mobile.invisible:
                mergeAppearance( rv, self.mobile.appearance() )
            else:
                appie = self.mobile.appearance()
                appie['fg'] = 'black'
                mergeAppearance( rv, appie )
        if self.trap and self.trap.canSpot( self.context.player ):
            rv['bg'] = 'red'
        rv['fg'] = "bold-" + rv['fg']
        return rv
    def appearanceRemembered(self):
        return {
            'ch': self.symbol,
            'fg': self.fgColour,
            'bg': self.bgColour,
        }
    def getRelative(self, dx, dy):
        return self.level.get( self.x + dx, self.y + dy )
    def neighbours(self):
        return [ self.getRelative(dx,dy) for dx in (-1,0,1) for dy in (-1,0,1) if dx or dy ]
    def describeItems(self):
        import grammar
        if self.items:
            ent = []
            stacked = countItems( self.items )
            return capitalizeFirst( grammar.makeCountingList( stacked ) )
        return ""
    def describeHere(self):
        ent = []
        if self.ceilingHole:
            ent.append( "There's a hole in the ceiling above you." )
        itemlist = self.describeItems()
        if itemlist:
            ent.append( itemlist )
            if len( self.items ) > 1:
                ent.append( "are" )
            else:
                ent.append( "is" )
            ent.append( "here." )
        if ent:
            self.context.log( " ".join( ent ) )
    def opaque(self):
        if self.mobile and self.mobile.hindersLOS:
            return True
        return self.hindersLOS
    def remember(self):
        import copy
        if not self.rememberedAs or self.rememberedAs.name != self.name:
            self.rememberedAs = copy.copy( self )
            self.rememberedAs.items = []
            self.rememberedAs.mobile = None
    def diggable(self):
        return not self.isBorder

def cannotCloseDoorBecause( tile ):
    if not tile.isDoor:
        return "there's no door there"
    if tile.doorState != "open":
        return "it's already closed"
    if tile.items:
        return "there's something in the way"
    if tile.mobile:
        return "there's a creature in the way"
    return ""

def closeDoor( tile ):
    assert not cannotCloseDoorBecause( tile )
    makeClosedDoor( tile )

def openDoor( tile ):
    # this is done by bumping so we don't need error messages
    assert tile.isDoor
    makeOpenDoor( tile )

def makeStairsDown( tile ):
    tile.name = "stairs down"
    tile.symbol = ">"
    tile.fgColour = "white"
    tile.bgColour = "black"
    tile.impassable = False
    tile.spawnMonsters = False
    tile.spawnItems = False
    tile.level.stairsDown = tile
    tile.tileTypeDesc = "Stairs leading down to the dungeon below."
    
def makeStairsUp( tile, isPortal = False ):
    if isPortal:
        tile.name = "magical portal"
        tile.symbol = "O"
        tile.fgColour = "black"
        tile.bgColour = "magenta"
        tile.impassable = True
        tile.spawnMonsters = False
        tile.spawnItems = False
        tile.tileTypeDesc = "The magical portal leading back to the University Library."
        tile.isPortal = True
    else:
        tile.name = "stairs up"
        tile.symbol = "<"
        tile.fgColour = "white"
        tile.bgColour = "black"
        tile.impassable = False
        tile.spawnMonsters = False
        tile.spawnItems = False
        tile.tileTypeDesc = "Stairs leading up to the shallower parts of the dungeon."
    tile.level.stairsUp = tile

def makeImpenetrableRock( tile ):
    tile.name = "rock"
    tile.symbol = " "
    tile.fgColour = "white"
    tile.bgColour = "black"
    tile.impassable = True
    tile.spawnMonsters = False
    tile.spawnItems = False
    tile.hindersLOS = True
    tile.tileTypeDesc = ""

def makeClosedDoor( tile ):
    tile.name = "closed door"
    tile.symbol = "+"
    tile.fgColour = "black"
    tile.bgColour = "yellow"
    tile.impassable = True
    tile.spawnMonsters = False
    tile.spawnItems = False
    tile.hindersLOS = True
    tile.isDoor = True
    tile.doorState = "closed"
    tile.tileTypeDesc = "A closed door."

def makeOpenDoor( tile ):
    tile.name = "open door"
    tile.symbol = "+"
    tile.fgColour = "yellow"
    tile.bgColour = "black"
    tile.impassable = False
    tile.spawnMonsters = False
    tile.spawnItems = False
    tile.hindersLOS = False
    tile.isDoor = True
    tile.doorState = "open"
    tile.tileTypeDesc = "An open door."

def makeHallway( tile ):
    tile.name = "passage floor"
    tile.symbol = "."
    tile.fgColour = "white"
    tile.bgColour = "black"
    tile.impassable = False
    tile.spawnMonsters = False
    tile.spawnItems = False
    tile.hindersLOS = False
    tile.tileTypeDesc = "A narrow passage."

def makeFloor( tile ):
    tile.name = "floor"
    tile.symbol = "."
    tile.fgColour = "white"
    tile.bgColour = "black"
    tile.impassable = False
    tile.spawnMonsters = True
    tile.spawnItems = True
    tile.hindersLOS = False
    tile.tileTypeDesc = ""
    tile.isDoor = False

def makeWall( tile ):
    tile.name = "wall"
    tile.symbol = "#"
    tile.fgColour = "white"
    tile.bgColour = "black"
    tile.impassable = True
    tile.spawnMonsters = False
    tile.spawnItems = False
    tile.hindersLOS = True
    tile.tileTypeDesc = "A wall."
    tile.isDoor = False

class Mobile:
    # this class is a mess, there are several player-specific fields
    def __init__(self,
                 name,
                 symbol,
                 hitpoints = 5,
                 speed = Speed.Normal,
                 tile = None,
                 ai = None,
                 context = None,
                 fgColour = 'white',
                 bgColour = None,
                 attackVerb = Verb( "attack" ),
                 attackElaboration = "",
                 weightLimit = 60,
                 flying = False,
                 groundhugger = False,
                 rarity = None,
                 proto = True,
                 meleePower = 1,
                 onDeath = None,
                 hindersLOS = False, # behaviour flags
                 nonalive = False,
                 walking = True,
                 swimming = False,
                 pushable = False,
                 destroyedByDigging = False,
                 incorporeal = False,
                 isBoulder = False,
                 essential = False,
                 chesspiece = False,
                 spawner = None,
                 noChildren = None,
                ):
        assert fgColour != 'red' # used for traps
        self.rarity = rarity
        assert isinstance( rarity, Rarity )
        self.name = name
        self.hindersLOS = hindersLOS
        self.symbol = symbol
        self.fgColour = fgColour
        self.bgColour = bgColour
        self.tile = None
        self.dead = False
        self.scheduledAction = None
        self.speed = speed
        self.chesspiece = chesspiece
        self.ai = ai
        self.inventory = []
        self.noSchedule = False
        self.nonalive = nonalive
        self.weightLimit = weightLimit
        self.hitpoints = hitpoints
        self.maxHitpoints = hitpoints
        self.flying = flying
        self.groundhugger = groundhugger
        self.meleePower = meleePower
        self.cachedFov = []
        self.isBoulder = isBoulder
        self.trapDetection = 0
        self.essential = essential
            # I'm trying to avoid using HP a lot. The amounts of HP
            # in the game will be low, e.g.: 5-20 for the player, not hundreds.
            # Basically, the goal is: if you take damage, you've made a mistake,
            # but one we're not as strict about. More severe mistakes get instakills
            # (walking into a spike pit).
        self.attackVerb = attackVerb
        self.attackElaboration = attackElaboration
        self.spellbook = []
        self.weapon = None
        self.buffs = {}
        self.lastBuffCheck = None
        self.walking = walking
        self.swimming = swimming
        self.pushable = pushable
        self.pacified = False
        self.destroyedByDigging = destroyedByDigging
        self.invisible = False
        self.unattackable = False
        self.visions = False
        self.stunned = False
        self.generated = 0
        self.debugname = "(spawned from no method)"
        self.incorporeal = incorporeal
        self.deathHooks = []
        self.manaUsed = 0
        self.greatestDepth = 0
        self.spawnCount = 0
        self.killCount = 0
        self.directKillCount = 0
        self.protomonster = self
        self.lifesense = False
        self.spawner = spawner
        self.noChildren = noChildren
        self.protector = None
        self.childrenAttacked = False
        self.trappedFor = 0
        self.children = []
        if onDeath:
            self.deathHooks.append( onDeath )
        if not proto:
            self.context = context
            self.moveto( tile, neverfail = True )
    def itemTypeCount(self, kind):
        return len( list( filter( lambda item: item.itemType == kind, self.inventory ) ) )
    def spawn(self, context, tile ):
        self.spawnCount +=1
        import copy
        self.generated += 1
        rv = copy.copy( self )
        rv.protomonster = self
        rv.debugname = "%s#%d" % (self.name.singular, self.generated)
        # this shallow copy causes SO MANY problems
        rv.name = self.name.selectGender()
        if self.ai:
            rv.ai = copy.copy( self.ai )
        rv.buffs = {}
        rv.context = context
        rv.sim = tile.level.sim
        rv.moveto( tile, neverfail = True )
        if rv.spawner:
            noCh = random.randint( *rv.noChildren )
            rv.children = []
            for i in range(noCh):
                tile = rv.tile.level.getClearTileAround( rv.tile )
                rrv = rv.spawner.spawn( context, tile )
                rrv.protector = rv
                rv.children.append( rrv )
        return rv
    def hasMacGuffin(self):
        mgs = [ item for item in self.inventory if item.isMacGuffin ]
        return len(mgs) > 0
    def inventoryGive(self, item):
        item.entersInventory( self )
        self.inventory.append( item )
    def inventoryTake(self, item):
        item.leavesInventory( self )
        self.inventory.remove( item )
        return item
    def addBuff(self, buff, timespan):
        try:
            self.buffs[buff] += timespan
            buff.buff( self, novel = False )
        except KeyError:
            self.buffs[buff] = timespan
            buff.buff( self, novel = True )
    def lifesensible(self): # yes, the name is just silliness
        # debating whether to allow nonalive creatures
        # also, what about abstracts like chesspieces?
        # probably best to allow all
        # but definitely not boulders.
        return not self.isBoulder
    def inventoryWeight(self):
        return (self.weapon.weight if self.weapon else 0) + sum( [ item.weight for item in self.inventory ] )
    def payForSpell(self, cost):
        if not self.weapon or not self.weapon.magical:
            self.context.log( "You don't have a staff or a wand handy.." )
        else:
            if cost <= self.weapon.mana:
                self.manaUsed += cost
                self.weapon.mana -= cost
                return True
            self.context.log( "There's not enough energy left in your %s to cast that." % self.weapon.name.singular )
        if self.context.game.main.query( SelectionMenuWidget,
                                         choices = [ (True, "Yes"), (False, "No") ],
                                         title = "Draw on your inner magical energy to cast?",
                                         padding = 5, ):
            self.maxHitpoints -= 1
            self.hitpoints = min( self.hitpoints, self.maxHitpoints )
            self.damage(0) # check for death
            return True
        return False
    def describe(self):
        statuses = self.monsterstatus()
        if statuses:
            statuses = ", " + statuses
        return capitalizeFirst( "%s (%d/%d hp%s)." % (self.name.indefiniteSingular(), self.hitpoints, self.maxHitpoints, statuses ) )
    def damage(self, n, fromPlayer = False, noMessage = False):
        if self.unattackable:
            return
        if self.essential:
            return
        self.hitpoints -= n
        if self.hitpoints <= 0:
            if not noMessage:
                self.killmessage( fromPlayer, usePronoun = "subject" )
            self.kill()
    def canBeMeleeAttackedBy(self, mobile):
        # levitating creatures are out of reach for groundhuggers
        if self.unattackable:
            return False
        if self.flying and (mobile.groundhugger and not mobile.flying):
            return False
        return True
    def meleeAttack(self, target):
        verb, elab = self.attackVerb, self.attackElaboration
        if target.chesspiece:
            verb, elab = Verb( "capture", "captures" ), ""
        self.logVisual( "You %s %s%s!" % (verb.second(), target.name.definiteSingular(), elab ),
                        "%s " + verb.third() + " " + ("you" if target.isPlayer() else target.name.definiteSingular()) + elab + "!" 
        )
        if target.ai:
            if self.isPlayer(): # infighting: not a 7DRL feature
                target.ai.provoked = True
                if target.protector:
                    target.protector.childrenAttacked = True
        if self.weapon:
            target.damage( self.weapon.damage, noMessage = target.chesspiece )
        else:
            target.damage( self.meleePower, noMessage = target.chesspiece )
        if self.isPlayer() and target.dead:
            target.protomonster.directKillCount += 1
    def monsterstatus(self):
        rv = []
        if self.stunned:
            rv.append( "stunned" )
        if self.pacified:
            rv.append( "pacified" )
        if self.flying:
            rv.append( "flying" )
        if self.incorporeal:
            rv.append( "incorporeal" )
        return ", ".join( rv )
    def status(self):
        rv = []
        # stun is not a player-applicable status
        if self.unattackable:
            rv.append( "Rockform" )
        if self.flying:
            rv.append( "Flying" )
        if self.invisible:
            rv.append( "Invisible" )
        if self.visions:
            rv.append( "Visions" )
        if self.lifesense:
            rv.append( "Lifesense" )
        if self.trappedFor > 0:
            rv.append( "Trapped" )
        return " ".join( rv )
    def webtrap(self, turns):
        self.trappedFor += turns
    def moveto(self, tile, turbulenceProbability = 1.0, neverfail = False):
        assert not tile.cannotEnterBecause( self )
        if neverfail:
            self.trappedFor = 0
        if self.trappedFor > 0:
            if self.flying:
                self.trappedFor = 0
                self.logVisual( "You fly out of the pit.", "%s flies out of the pit." )
            else:
                self.trappedFor -= 1
                if self.trappedFor > 0:
                    self.logVisual( "You struggle to get out of the pit.", "%s struggles to get out of the pit." )
                    return
                self.logVisual( "You manage to get out of the pit.", "%s manages to get out of the pit." )
        if self.tile:
            self.tile.leaves()
        if not self.tile or self.tile.level != tile.level:
            if self.scheduledAction:
                self.scheduledAction.cancel()
                self.scheduledAction = None
            self.tile = tile
            self.greatestDepth = max( self.greatestDepth, self.tile.level )
            self.schedule()
        else:
            if self.tile and self.tile.level == tile.level and self.isPlayer():
                self.tile.playerTrail = tile
            self.tile = tile
        self.tile.enters( self, turbulenceProbability = turbulenceProbability )
    def isPlayer(self):
        try:
            return self.context.player == self
        except AttributeError:
            return False
    def appearance(self):
        rv = {
            'ch': self.symbol,
            'fg': self.fgColour
        }
        if self.bgColour:
            rv[ 'bg' ] = self.bgColour
        return rv
    def logAural(self, youMessage):
        self.context.log( youMessage )
        return True
    def logVisualMon(self, someoneMessage, usePronoun = False):
        return self.logVisual( None, someoneMessage, usePronoun = usePronoun )
    def logVisual(self, youMessage, someoneMessage, usePronoun = False):
        try:
            if self.context.player.tile.level != self.tile.level:
                return
        except AttributeError:
            return
        if self.isPlayer():
            self.context.log( youMessage )
            return True
        elif (self.tile.x,self.tile.y) in self.context.player.cachedFov:
            if usePronoun:
                self.context.log( someoneMessage % self.name.pronounSubject() if usePronoun == "subject" else self.name.pronounObject() )
            else:
                self.context.log( someoneMessage % self.name.definiteSingular() )
            return True
        return False
    def killmessage(self, active = False, usePronoun = "subject"):
        if not active:
            message = "%s dies!"
            if self.nonalive:
                message = "%s is destroyed!"
        else:
            message = "You kill %s!"
            if self.nonalive:
                message = "You destroy %s!"
        self.logVisual( "You die...", message, usePronoun = usePronoun )
    def kill(self, noTriggerHooks = False):
        if self.essential:
            print >> sys.stderr, "warning: saving essential monster", self.debugname
            return
        if self.dead:
            return
        self.dead = True
        self.protomonster.killCount += 1
        if not noTriggerHooks:
            for hook in self.deathHooks:
                hook.onDeath( self )
        for item in self.inventory: #hooks ? yes/no?
            self.tile.items.append( item )
        self.inventory = []
        if self.scheduledAction:
            self.scheduledAction.cancel()
        if self.isPlayer():
            raise PlayerKilledException()
#        print >> sys.stderr, self.debugname, "shuffling coil from", self.tile.x, self.tile.y
        self.tile.leaves()
        self.noSchedule = True # likely we're actually call-descendants of .trigger(), so blanking
                               # the scheduled action is not enough
    def schedule(self):
        if not self.noSchedule and not self.scheduledAction:
            self.scheduledAction = self.tile.level.sim.schedule( self, self.tile.level.sim.t + self.speed )
    def checkBuffs(self, t):
        if not self.lastBuffCheck:
            self.lastBuffCheck = t
        dt = t - self.lastBuffCheck
        self.lastBuffCheck = t
        for buff in self.buffs.keys():
            self.buffs[buff] -= dt
            if self.buffs[buff] < 0:
                buff.debuff( self )
    def trigger(self, t):
#        if self.ai:
#            print >> sys.stderr, self.debugname, "triggering"
        self.checkBuffs( t )
        if not self.stunned:
            if self.ai:
                if self.pacified:
                    from ai import RandomWalker
                    RandomWalker(avoidTraps = True).trigger( self )
                else:
                    self.ai.trigger( self )
        if not self.noSchedule:
            self.scheduledAction = self.tile.level.sim.schedule( self, t + self.speed )
        else: # wait, what?
            self.scheduledAction = None
    def fov(self, radius = None, setRemembered = False):
        from vision import VisionField
        rv = VisionField( self.tile,
                            lambda tile : tile.opaque(),
                            mark = None if not setRemembered else lambda tile : tile.remember()
        ).visible
        self.cachedFov = rv
        return rv

class Item:
    def __init__(self, name, symbol, fgColour, bgColour = None, itemType = None, weight = None, rarity = None, isMacGuffin = False):
        self.rarity = rarity
        assert isinstance( self.rarity, Rarity )
        self.name = name
        self.symbol = symbol
        self.fgColour = fgColour
        self.bgColour = bgColour
        self.itemType = name.singular if not itemType else itemType
        self.weight = weight
        self.isMacGuffin = isMacGuffin
        self.inventoryHooks = []
    def spawn(self):
        import copy
        return copy.copy( self )
    def stackname(self):
        return self.name
    def appearance(self):
        rv = {
            'ch': self.symbol,
            'fg': self.fgColour
        }
        if self.bgColour:
            rv[ 'bg' ] = self.bgColour
        return rv
    def entersInventory(self, mobile):
        for hook in self.inventoryHooks:
            hook.onEnterInventory( mobile )
    def leavesInventory(self, mobile):
        for hook in self.inventoryHooks:
            hook.onLeaveInventory( mobile )

class Map:
    def __init__(self, context, width, height):
        self.x0, self.y0 = 0, 0
        self.context = context
        self.w, self.h = width, height
        self.tiles = {}
        for i in range(self.w):
            for j in range(self.h):
                self.tiles[i,j] = Tile(context,self, i,j)
                if i == 0 or j == 0 or (i+1) == self.w or (j+1) == self.h:
                    self.tiles[i,j].isBorder = True
        self.mobiles = []
        self.items = [] # NOTE: items on ground, not items kept in mobiles, containers or otherwise
        self.sim = timing.Simulator()
        self.previousLevel = None
        self.nextLevel = None
    def doRectangle(self, f, x0, y0, w, h):
        for x in range(x0, x0 + w):
            for y in range(y0, y0 + h):
                f( self.tiles[x,y] )
    def get(self, x, y):
        try:
            return self.tiles[x,y]
        except KeyError:
            return None
    def randomTile(self, criterion = lambda tile : True):
        import random
        choices = list( filter( criterion, self.tiles.values() ) )
        if not choices:
            return None
        return random.choice( choices )
    def spawnMobile(self, cls, *args, **kwargs):
        tile = self.randomTile( lambda tile : tile.spawnMonsters and not tile.mobile and not tile.trap )
        assert tile != None
        rv = cls( tile = tile, proto = False, *args, **kwargs )
        return rv
    def spawnItem(self, cls, *args, **kwargs):
        tile = self.randomTile( lambda tile : tile.spawnItems )
        assert tile != None
        rv = cls( *args, **kwargs )
        tile.items.append( rv )
        return rv
    def scatterItemsAround(self, items, origin):
        for item in items:
            tile = self.getClearTileAround( origin )
            tile.items.append( item )
    def getClearTileAround(self, origin, goal = lambda tile: not tile.impassable and not tile.mobile):
        from pathfind import Pathfinder, infinity
        import math
        pf = Pathfinder(cost = lambda tile : 1,
                        goal = goal,
                        heuristic = lambda tile : 0,
        )
        pf.addOrigin( origin )
        path = pf.seek()
        return path[-1]
    def getPlayerSpawnSpot(self, upwards = False):
        # around the stairs?
        return self.getClearTileAround( self.stairsDown if upwards else self.stairsUp )
    def generateDeeperLevel(self):
        if self.nextLevel:
            return self.nextLevel
        self.nextLevel = mapFromGenerator( self.context, self )
        return self.nextLevel

def mapFromGenerator( context, ancestor = None):
    from levelgen import generateLevel
    lg = generateLevel( 80, 
                        50,
                        (16,30,16,30),
                        (12,20,12,16)
    )
    rv = Map( context, lg.width, lg.height )
    if ancestor:
        rv.previousLevel = ancestor
        ancestor.nextLevel = rv
        rv.depth = ancestor.depth + 1
    else:
        rv.depth = 1
        rv.nextLevel = None
    # Ror now just the cell data is used; do recall that the lg object
    # also contains .rooms; these make up a graph that can be used to
    # classify the rooms.
    for x in range( lg.width ):
        for y in range( lg.height ):
            {
                ' ': makeImpenetrableRock,
                '+': lambda tile: makeOpenDoor(tile) if random.random() > 0.5 else makeClosedDoor(tile),
                'o': makeHallway,
                '.': makeFloor,
                '#': makeWall,
            }[ lg.data[y][x] ]( rv.tiles[x,y] )
    makeStairsUp( rv.tiles[ lg.entryRoom.internalFloorpoint() ], isPortal = not ancestor )
    makeStairsDown( rv.tiles[ lg.exitRoom.internalFloorpoint() ] )
    if rv.depth == DungeonDepth:
        tile = rv.randomTile( lambda tile : not tile.cannotEnterBecause( context.macGuffinMobile ) and lg.exitRoom.contains( tile.x, tile.y )  )
        monster = context.macGuffinMobile.spawn( context, tile )
    for room in lg.rewardRooms:
        # should be in chests: that way it's hard to
        # distinguish between danger rooms and reward rooms
        valueTarget = 40 # per room, people!
        for protoitem in selectThings( rv.depth, valueTarget, context.protoitems ):
            item = protoitem.spawn()
            tile = rv.tiles[ room.internalFloorpoint() ]
            tile.items.append( item )
    for room in lg.dangerRooms:
        generateTrapsForRoom( rv, context, room )
    monsterValueTarget = random.randint( 8, 12 )
    for protomonster in selectThings( rv.depth, monsterValueTarget, context.protomonsters ):
        tile = rv.randomTile( lambda tile : not tile.cannotEnterBecause( protomonster ) and not lg.entryRoom.contains( tile.x, tile.y )  )
        monster = protomonster.spawn( context, tile )
    noBoulders = random.randint( 0, 5 )
    from monsters import Boulder
    for i in range( noBoulders ):
        tile = rv.randomTile( lambda tile : not tile.cannotEnterBecause( Boulder ) )
        monster = Boulder.spawn( context, tile )
    context.levels.append( rv )
    return rv

def innerRectangle( o, n = 0):
    return o.x0 + n, o.y0 + n, o.w - 2*n, o.h - 2*n

def mergeAppearance( result, target ):
    for key, val in target.items():
        result[ key ] = val

def sign( n ):
    if n > 0: return 1
    if n < 0: return -1
    return 0


def bresenhamCircle( origin, radius ):
    cx, cy = origin
    rv = set( [(cx, cy+radius), (cx,cy-radius), (cx+radius,cy), (cx-radius,cy)] )
    f = 1 - radius
    ddfx = 1
    ddfy = -2 * radius
    x, y = 0, radius
    while x < y:
        if f >= 0:
            y -= 1
            ddfy += 2
            f += ddfy
        x += 1
        ddfx += 2
        f += ddfx
        rv.add( (cx+x, cy+y) )
        rv.add( (cx-x, cy+y) )
        rv.add( (cx-x, cy-y) )
        rv.add( (cx+x, cy-y) )
        rv.add( (cx+y, cy+x) )
        rv.add( (cx-y, cy+x) )
        rv.add( (cx-y, cy-x) )
        rv.add( (cx+y, cy-x) )
    return rv

def disk( origin, radius ):
    cx, cy = origin
    rv = set()
    for x in range(-radius,radius+1):
        for y in range(-radius,radius+1):
            if x*x + y*y <= radius*radius:
                rv.add( (cx+x,cy+y) )
    return rv
                
def expandingDisk( origin, size ):
    for r in range( 1, size + 1 ):
        yield disk( origin, r )

def expandingCircle( origin, size ):
    for r in range( 1, size ):
        yield bresenhamCircle( origin, r )

class Viewport:
    def __init__(self, level, window, visibility = lambda tile : True ):
        self.visibility = visibility
        self.window = window # set new on resize
        self.level = level
    def paint(self, cx, cy, effects = {}, highlight = None):
        x0 = cx - int(self.window.w / 2)
        y0 = cy - int(self.window.h / 2)
        for x in range(x0, x0 + self.window.w):
            for y in range(y0, y0 + self.window.h):
                darkness = { 'ch': ' ', 'fg': 'black', 'bg': 'black' }
                try:
                    tile = self.level.tiles[x,y]
                except KeyError:
                    tile = None
                if effects.has_key( (x,y) ):
                    outgoing = effects[ x, y ]
                elif tile and self.visibility( tile ):
                    outgoing = tile.appearance()
                elif tile and tile.rememberedAs:
                    outgoing = tile.rememberedAs.appearanceRemembered()
                else:
                    outgoing = darkness
                if highlight and x == cx and y == cy:
                    if outgoing['fg'] != outgoing['bg']:
                        outgoing['fg'], outgoing['bg'] = outgoing['bg'], outgoing['fg']
                    else:
                        outgoing['fg'] = 'white'
                        outgoing['bg'] = 'white'
                self.window.put( x - x0, y - y0, **outgoing )
