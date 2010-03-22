from harmless7drl import Widget
from level import *
from widgets import *
from textwrap import TextWrapper
from grammar import *
import timing
import magic

from serialization import GameContext
from level import PlayerKilledException, PlayerWonException
from plot import writeReport

class GameWidget ( Widget ):
    def __init__(self, *args, **kwargs):
        Widget.__init__( self, *args, **kwargs )
        name = self.main.query( TextInputWidget, 32, okay = string.letters, query = "Please enter your name: ", centered = True )
        self.context = GameContext()
        self.context.game = self
        self.initialized = False
        try:
            from harmless7drl import loadOldGame
            context = loadOldGame( name )
            wasLoaded = True
        except IOError:
            from harmless7drl import beginNewGame
            gender = self.main.query( SelectionMenuWidget, choices = [
                ('female', "Female"),
                ('male', "Male"),
            ], padding = 5, centered = True, title = "Please select your gender:", noInvert = True )
            context = beginNewGame( self.context, name, gender )
            wasLoaded = False
            from plot import displayIntro
            self.context = context
            displayIntro( self )
        self.context = context
        self.initialized = True
        self.name = None
        self.player = context.player
        context.game = self
        self.context = context
        self.cursor = None
        self.movementKeys = {
            'h': (-1, 0),
            'l': (1, 0),
            'j': (0, 1),
            'k': (0, -1),
            'y': (-1, -1),
            'u': (1, -1),
            'b': (-1, 1),
            'n': (1, 1),
            'west': (-1, 0),
            'east': (1, 0),
            'south': (0, 1),
            'north': (0, -1),
            'northwest': (-1, -1),
            'northeast': (1, -1),
            'southwest': (-1, 1),
            'southeast': (1, 1),
        }
        self.textfieldheight = 4
        screenw, screenh = self.ui.dimensions()
        self.turnlogWrapper = TextWrapper( screenw, self.textfieldheight )
        self.turnlogLines = []
        self.restrictVisionByFov = True
        self.visualEffects = {}
        self.proposedPath = None
        self.startled = False
        if wasLoaded:
            self.log( "Welcome back!" )
    def takePathStep(self):
        if self.proposedPath:
            tile = self.proposedPath.pop(0)
            if not tile.cannotEnterBecause( self.player ):
                self.player.moveto( tile )
                self.tookAction( 1 )
                return True
            self.proposedPath = None
        return False
    def log(self, s):
        self.turnlogWrapper.feed( s + " " )
        while self.turnlogWrapper.pages:
            self.turnlogLines = self.turnlogWrapper.popPage()
            self.main.query( HitEnterWidget )
        self.turnlogLines = []
        for i in range(self.textfieldheight):
            self.turnlogLines.append( self.turnlogWrapper.line(i) )
    def resized(self, screenw, screenh):
        # quirk: will lose data in text field when resizing
        self.turnlogWrapper = TextWrapper( screenw, self.textfieldheight )
    def clearlog(self):
        screenw, screenh = self.ui.dimensions()
        self.turnlogWrapper = TextWrapper( screenw, self.textfieldheight )
        self.turnlogLines = []
    def playerWon(self):
        from plot import displayOutro
        writeReport( self, True, self.player.itemTypeCount( 'spellbook' ) )
        displayOutro( self, self.player.itemTypeCount( 'spellbook' ) )
        self.done = True
        self.result = False
    def playerDied(self, pke):
        writeReport( self, False, didQuit = pke.didQuit )
        if not pke.didQuit: # if we quit, we just confirmed in a menu
            self.main.query( HitEnterWidget )
        self.done = True
        self.result = False
    def playerVisibility(self, fov):
        def visibility( tile ):
            visionsRadius = 12
            if (tile.x, tile.y) in fov:
                return True
            if self.player.visions and self.player.tile.withinRadiusFrom( tile, visionsRadius ):
                return True
            if self.player.lifesense and tile.mobile and tile.mobile.lifesensible():
                return True
            return False
        return visibility
    def draw(self):
        import time
        statusbarHeight = 2
        screenw, screenh = self.ui.dimensions()
        fov = self.player.fov( setRemembered = True )
        visibility = self.playerVisibility( fov )
        if not self.restrictVisionByFov:
            visibility = lambda tile : True
        vp = Viewport( level = self.player.tile.level,
                       window = Subwindow( self.ui, 0,
                       self.textfieldheight,
                       screenw,
                       screenh - self.textfieldheight - statusbarHeight),
                       visibility = visibility,
        )
        if self.cursor:
            x, y = self.cursor
        else:
            x, y = self.player.tile.x, self.player.tile.y
        vp.paint( x, y, effects = self.visualEffects, highlight = bool( self.cursor ) )
        for i in range( self.textfieldheight ):
            try:
                self.ui.putString( 0, i, self.turnlogLines[i], 'bold-white')
            except IndexError:
                pass
        sby = screenh - 2
        sbx = self.ui.putString( 0, sby, str(self.player.name), 'bold-white' )
        sbx = self.ui.putString( sbx + 5, sby, "HP: %d/%d" % (self.player.hitpoints, self.player.maxHitpoints), 'bold-white' )
        sbx = self.ui.putString( sbx + 5, sby, "DL: %d" % (self.player.tile.level.depth), 'bold-white' )
        if self.player.weapon:
            sbx = self.ui.putString( sbx + 5, sby, "Pw: %d (%s)" % (self.player.weapon.mana, self.player.weapon.name.singular), 'bold-white' )
        else:
            sbx = self.ui.putString( sbx + 5, sby, "Pw: none", 'bold-white' )
        sbx = self.ui.putString( sbx + 5, sby, "W: %0.2lf%%" % (self.player.inventoryWeight()*100.0/self.player.weightLimit), 'bold-white' )
        if self.player.status():
            sbx = self.ui.putString( sbx + 5, sby, self.player.status(), 'bold-white' )
    def advanceTime(self, dt):
        self.context.totalTime += dt
        self.player.tile.level.sim.advance( dt )
        while True:
            ev = self.player.tile.level.sim.next()
            if not ev:
                break
            ev.trigger()
    def tookAction(self, weight):
        self.advanceTime( self.player.speed * weight )
    def wait(self):
        self.log( "You wait." )
        self.tookAction( 1 )
    def tryPush(self, pushable, dx, dy):
        target = pushable.tile.getRelative( dx, dy )
        if pushable.ai.inMotion():
            self.context.log( "You can't push %s while %s's in motion!" % ( pushable.name.definiteSingular(), pushable.name.pronounObject() ) )
        elif (not target) or (target.cannotEnterBecause( pushable ) and not (target.mobile and target.mobile.trappedFor > 0 and not target.mobile.essential)):
            self.context.log( "You try to push %s but can't budge it." % pushable.name.definiteSingular() )
            self.tookAction( 1 )
        else:
            self.context.log( "You push %s." % pushable.name.definiteSingular() )
            if target.mobile:
                target.mobile.logVisual( "You are crushed beneath the boulder!", "%s is crushed beneath the boulder!" )
                target.mobile.kill()
            tile = pushable.tile
            pushable.moveto( target, neverfail = True )
            if not tile.cannotEnterBecause( self.player ):
                self.player.moveto( tile )
            self.tookAction( 1 )
    def tryMoveAttack(self, dx, dy):
        tile = self.player.tile.getRelative( dx, dy )
        if not tile:
            # At some point I encounteded this. Fairly sure that shouldn't happen.
            print >>sys.stderr, "warning: tile not present"
        else:
            if not tile.cannotEnterBecause( self.player ):
                self.player.moveto( tile )
                self.player.tile.describeHere()
                self.tookAction( 1 )
            elif tile.isPortal:
                if self.player.hasMacGuffin():
                    raise PlayerWonException()
                else:
                    self.log( "You can't turn back now." )
            elif tile.mobile:
                if tile.mobile.pushable:
                    self.tryPush( tile.mobile, dx, dy )
                elif tile.mobile.essential:
                    # warning: hilarity would ensue if any other essential objects were introduced
                    from plot import convertMacGuffin
                    convertMacGuffin( tile.mobile )
                elif tile.mobile.canBeMeleeAttackedBy( self.player ):
                    target = tile.mobile
                    self.player.meleeAttack( target )
                    if target.chesspiece and not tile.cannotEnterBecause( self.player ):
                        self.player.moveto( tile )
                    self.tookAction( 1 )
                else:
                    self.context.log( "You can't reach %s." % tile.mobile.name.pronounObject() )
            elif tile.isDoor and tile.doorState == "closed":
                self.log( "You open the door." )
                openDoor( tile )
                self.tookAction( 1 )
            else:
                reason = tile.cannotEnterBecause( self.player )
                if reason == "tile is impassable":
                    self.log( "There's a wall in the way." )
                else:
                    self.log( "You can't move there because %s." % reason )
    def pickup(self):
        if self.player.tile.items:
            if len( self.player.tile.items ) == 1:
                item = self.player.tile.items[0]
            else:
                stacked = countItems( self.player.tile.items )
                item = self.main.query( SelectionMenuWidget, choices = [
                    (items[0], name.amount( len(items), informal = True )) for name, items in stacked.items()
                ] + [ (None, "nothing") ], title = "Pick up what?", padding = 5 )
                if not item:
                    return
            if (self.player.inventoryWeight() + item.weight) < self.player.weightLimit:
                self.player.tile.items.remove( item )
                self.log( "You pick up %s." % item.name.definiteSingular() )
                self.player.inventoryGive( item )
                self.tookAction( 1 )
            else:
                self.log( "Being overburdened, you fail to pick up %s." % item.name.definiteSingular() )
                self.tookAction( 1 ) # since you can gain info this way: e.g. container full / empty
    def closeDoor(self):
        eligibleDoors = [ n for n in self.player.tile.neighbours() if not cannotCloseDoorBecause(n) ]
        if not eligibleDoors:
            self.log( "There's no open door within reach." )
        else:
            if len( eligibleDoors ) > 1:
                self.log( "Which door?" )
                dx, dy = self.main.query( DirectionWidget )
                door = self.player.tile.getRelative( dx, dy )
                if cannotCloseDoorBecause( door ):
                    self.log( "That's not an open door." )
                    return
            else:
                door = eligibleDoors[-1]
            closeDoor( door )
            self.log( "You close the door." )
            self.tookAction( 1 )
    def goUp(self):
        if self.player.tile.name == "stairs up":
            if self.player.tile.level.previousLevel:
                spot = self.player.tile.level.previousLevel.getPlayerSpawnSpot( upwards = True )
                self.player.moveto( spot, neverfail = True )
                self.tookAction( 1 )
            else:
                self.log( "For unspecified plot reasons, you don't want to turn back." )
        elif self.player.tile.ceilingHole:
            if not self.player.flying:
                self.log( "You can't reach the hole in the ceiling." )
            elif self.player.hasMacGuffin():
                # balance -- this would've been too easy
                self.log( "%s suddenly feels very heavy." % self.context.macGuffin.name.definiteSingular() )
                self.log( "Some sort of enchantment prevents you from flying through the hole in the ceiling carrying %s!" % self.context.macGuffin.name.definiteSingular() )
                self.tookAction( 1 )
            else:
                spot = self.player.tile.ceilingHole.level.getClearTileAround( self.player.tile.ceilingHole )
                self.player.moveto( spot, neverfail = True )
                self.log( "You fly through the hole in the ceiling." )
                self.tookAction( 1 )
        else:
            self.log( "You can't see any way to go up right here." )
    def goDown(self):
        if self.player.tile.name == "stairs down":
            nextLev = self.player.tile.level.generateDeeperLevel()
            spot = nextLev.getPlayerSpawnSpot()
            self.player.moveto( spot, neverfail = True )
            self.tookAction( 1 )
        elif self.player.flying and self.player.tile.trap and self.player.tile.trap.trapname == "trapdoor":
            if not self.player.flying:
                # impossible?
                self.player.tile.trap( self.player )
                self.tookAction( 1 )
            else:
                below = self.player.tile.trap.getTarget()
                spot = below.level.getClearTileAround( below )
                self.log( "You fly through the hole in the floor." )
                self.player.moveto( spot, neverfail = True )
                self.tookAction( 1 )
        else:
            self.log( "You can't see any way to go down right here." )
    def drop(self):
        if self.player.inventory:
            stacked = countItems( self.player.inventory )
            item = self.main.query( SelectionMenuWidget, choices = [
                (items[0], name.amount( len(items), informal = True )) for name, items in stacked.items()
            ] + [ (None, "nothing") ], title = "Drop what?", padding = 5 )
            if not item:
                return
            self.log( "You drop %s." % item.name.definiteSingular() )
            item = self.player.inventoryTake( item )
            self.player.tile.items.append( item )
            self.tookAction( 1 )
    def equipWeapon(self, weapon):
        assert weapon.itemType == 'weapon'
        if self.player.weapon:
            self.player.inventoryGive( self.player.weapon )
        self.player.weapon = weapon
        self.player.inventoryTake( weapon )
        self.log( "You wield %s." % weapon.name.definiteSingular() )
        self.tookAction( 1 )
    def unequipWeapon(self):
        if not self.player.weapon:
            return None # shouldn't happen
        self.player.inventoryGive( self.player.weapon )
        self.log( "You stop wielding your %s." % self.player.weapon.name.singular )
        self.player.weapon = None
        self.tookAction( 1 )
    def accessInventory(self):
        stacked = countItems( self.player.inventory )
        chosen = self.main.query( SelectionMenuWidget, choices = [
            (('unwield', weapon.name.indefiniteSingular() + " (wielded)")) for weapon in [self.player.weapon] if weapon
        ] + [
            (items[0], name.amount( len(items), informal = True )) for name, items in stacked.items()
        ] + [ (None, "cancel") ], padding = 5 )
        if chosen:
            if chosen == 'unwield':
                self.unequipWeapon()
            elif chosen.itemType == 'weapon':
                self.equipWeapon( chosen )
            elif chosen.itemType == 'talisman':
                self.log( "You merely need to carry %s for its magics to work." % chosen.name.definiteSingular() )
            elif chosen.itemType == 'rune':
                self.log( "The rune is useless on its own. (Press 'w' to combine runes into spells.)" )
            elif chosen.itemType == 'tome':
                if chosen.identifyRune( self.context, self.player.inventory ):
                    self.tookAction( 1 )
            elif chosen.itemType == 'healing':
                self.log( "You chug down the small vial of purple liquid." )
                if self.player.hitpoints < self.player.maxHitpoints:
                    self.player.hitpoints += 1
                    if self.player.hitpoints == self.player.maxHitpoints:
                        self.log( "You feel better." )
                    else:
                        self.log( "You feel a bit better." )
                self.player.inventory.remove( chosen )
                self.tookAction( 1 )
            elif chosen.itemType == 'spellbook':
                self.log( "It's of no use at the moment -- you need some more applicable magic." )
                self.log( "%s would probably appreciate it being returned to the library, though." % self.context.bossName.definiteSingular() )
            elif chosen.itemType == 'macguffin':
                self.log( "You don't see much of a use for %s." % self.context.macGuffin.name.definiteSingular() )
                self.log( "However, %s would probably appreciate getting %s back in one piece." % (self.context.bossName.definiteSingular(), self.context.macGuffin.name.pronounObject() ) )
            else:
                self.log( "You don't see how you could make use of %s." % chosen.name.definiteSingular() )
    def writeSpell(self):
        from magic import Spells
        goodSpells = list(filter( lambda spell: spell not in self.context.player.spellbook and spell.canBuild( self.context.player.inventory ), Spells ))
        if not goodSpells:
            self.log( "You don't have the runes at hand to write any new spells." )
        else:
            chosen = self.main.query( SelectionMenuWidget, choices = [
                (spell,spell.description) for spell in goodSpells
            ] + [ (None, "cancel") ], title = "Which spell do you want to write?", padding = 5 )
            if chosen:
                chosen.build( self.context.player.inventory )
                self.log( "You enter a magical trance as you begin scribing the %s spell..." % chosen.name )
                self.tookAction( 30 )
                self.log( "You have written the %s spell into your spellbook." % chosen.name )
                self.context.player.spellbook.append( chosen )
    def castSpell(self):
        if not self.context.player.spellbook:
            self.log( "Your spellbook is blank." )
        else:
            hotkeys = {}
            for spell in self.context.player.spellbook:
                hotkeys[spell.hotkey] = spell
            chosen = self.main.query( SpellSelectionMenuWidget, choices = [
                (spell,"%c: %s (%d)" % (spell.hotkey,spell.name,spell.cost())) for spell in self.context.player.spellbook
            ] + [ (None, "cancel") ], title = "Which spell do you want to cast?", padding = 5,
            hotkeys = hotkeys,
            )
            if chosen:
                if self.context.player.payForSpell( chosen.cost() ):
                    try:
                        chosen.cast( self.context ) # intransitive spells only at the moment
                        chosen.castCount += 1
                        self.tookAction( 1 )
                    except magic.CancelCasting:
                        pass
    def keyboard(self, key):
        try:
            try:
                dx, dy = self.movementKeys[ key ]
                self.clearlog()
                self.tryMoveAttack( dx, dy )
                return
            except KeyError:
                pass
            try:
                standardAction = None
                standardAction = {
                    '.': self.wait,
                    ',': self.pickup,
                    'd': self.drop,
                    'c': self.closeDoor,
                    '>': self.goDown,
                    '<': self.goUp,
                    'w': self.writeSpell,
                    'm': self.castSpell,
                    'i': self.accessInventory,
                }[key]
            except KeyError:
                pass
            from harmless7drl import DebugMode
            if standardAction:
                self.clearlog()
                standardAction()
            elif key == ':': # Look command
                self.main.query( CursorWidget, self )
            elif key == 'q':
                from harmless7drl import savefileName
                self.log( "Quitting, please wait..." )
                self.main.query( DelayWidget, 0 )
                self.context.save( savefileName( self.context.player.rawname ) )
                self.done = True
            elif key == 'Q':
                if self.main.query( SelectionMenuWidget, choices = [
                    (False, "No"),
                    (True, "Yes, quit without saving"),
                ], title = "Really give up on this character?", padding = 5 ):
                    raise PlayerKilledException( didQuit = True )
            elif key == '?':
                from plot import displayHelp
                displayHelp( self.main )
#            elif False:
            elif DebugMode and key == '!':
                if self.main.query( SelectionMenuWidget, choices = [
                    (False, "No"),
                    (True, "Yes"),
                ], title = "Enter debugging mode?", padding = 5 ):
                    self.context.debugmode = True
            elif self.context.debugmode:
                if key == 'W':
                    raise PlayerWonException()
                elif key == 'V':
                    self.restrictVisionByFov = not self.restrictVisionByFov
                elif key == 'D':
                    self.player.trapDetection += 1
                elif key == 'S':
                    from magic import Spells
                    for spell in Spells:
                        if spell not in self.player.spellbook:
                            self.player.spellbook.append( spell )
                    self.player.weapon.mana += 500
                elif key == 'H':
                    self.player.hitpoints += 1
                    self.player.maxHitpoints += 1
                elif key == 'X':
                    self.player.damage( 1 )
        except PlayerKilledException, pke:
            self.playerDied( pke )
        except PlayerWonException:
            self.playerWon()
    def showEffects(self, effects, t = 0.05):
        if not self.initialized:
            return
        try:
            fov = self.player.fov( setRemembered = True )
        except AttributeError:
            return # traps triggering before everything is set up
        seen = False
        for x,y in effects.keys():
            if (x,y) in fov:
                seen = True
                break
        if not seen:
            return
        self.visualEffects = effects
        self.main.query( DelayWidget, t )
        self.visualEffects = {}
    def showExplosion(self, origin, radius, distribution = ( 'red', 'yellow', 'red', 'red', 'yellow', 'yellow', 'white', 'black' ) ):
        if not self.initialized:
            return [] # hax
        cx, cy = origin
        fx = {}
        for region in expandingDisk( (cx, cy), radius):
            for x, y in region:
                fg, bg = random.sample( distribution, 2 )
                if random.randint(0,1):
                    fg = 'bold-' + fg
                fx[x,y] = {
                   'ch': random.choice( ['-', '.', '*', '`', '`' ] ),
                   'fg': fg,
                   'bg': bg,
                }
            self.showEffects( fx, 0.05 )
        return region
    def showStraightRay(self, origin, direction, radius, fg, bg, stopper = lambda xy : False, projectile = False ):
        if not self.initialized:
            return [] # hax
        cx, cy = origin
        dx, dy = direction
        ch = {
            (0,0): '*',
            (1,-1): '/',
            (1,0): '-',
            (1,1): '\\',
            (0,1): '|',
            (-1,1): '/',
            (-1,0): '-',
            (-1,-1): '\\',
            (0,-1): '|',
        }[direction]
        fx = {}
        rv = []
        for i in xrange( radius ):
            cx += dx
            cy += dy
            if projectile:
                rv = []
                fx = {}
            rv.append( (cx,cy) )
            fx[cx,cy] = {
                'ch': ch,
                'fg': fg,
                'bg': bg,
            }
            self.showEffects( fx, 0.05 )
            if stopper( (cx,cy) ):
                break
        return rv
