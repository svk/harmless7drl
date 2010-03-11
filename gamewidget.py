from core import Widget
from level import *
from widgets import *
from textwrap import TextWrapper
from grammar import *
import timing

class GameWidget ( Widget ):
    def __init__(self, context, *args, **kwargs):
        Widget.__init__( self, *args, **kwargs )
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
    def draw(self):
        import time
        statusbarHeight = 2
        screenw, screenh = self.ui.dimensions()
        fov = self.player.fov( setRemembered = True )
        if self.restrictVisionByFov:
            visibility = lambda tile : (tile.x, tile.y) in fov
        else:
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
        if self.player.status():
            sbx = self.ui.putString( sbx + 5, sby, self.player.status(), 'bold-white' )
    def advanceTime(self, dt):
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
    def tryMoveAttack(self, dx, dy):
        tile = self.player.tile.getRelative( dx, dy )
        if not tile:
            # At some point I encounteded this. Fairly sure that shouldn't happen.
            print "warning: tile not present"
        else:
            if not tile.cannotEnterBecause( self.player ):
                self.player.moveto( tile )
                self.tookAction( 1 )
            elif tile.mobile:
                if tile.mobile.canBeMeleeAttackedBy( self.player ):
                    self.player.meleeAttack( tile.mobile )
                    self.tookAction( 1 )
                else:
                    self.context.log( "You can't reach %s." % tile.mobile.pronounObject() )
            elif tile.isDoor and tile.doorState == "closed":
                self.log( "You open the door." )
                openDoor( tile )
                self.tookAction( 1 )
            else:
                self.log( "You can't move there because %s." % tile.cannotEnterBecause( self.player ) )
    def pickup(self):
        if self.player.tile.items:
            if len( self.player.tile.items ) == 1:
                item = self.player.tile.items.pop()
            else:
                stacked = countItems( self.player.tile.items )
                item = self.main.query( SelectionMenuWidget, choices = [
                    (items[0], name.amount( len(items), informal = True )) for name, items in stacked.items()
                ] + [ (None, "nothing") ], title = "Pick up what?", padding = 5 )
                if not item:
                    return
                self.player.tile.items.remove( item )
            self.player.inventory.append( item )
            self.log( "You pick up %s." % item.name.definiteSingular() )
            self.tookAction( 1 )
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
                self.player.moveto( spot )
                self.tookAction( 1 )
            else:
                self.log( "For unspecified plot reasons, you don't want to turn back." )
        elif self.player.tile.ceilingHole:
            if not self.player.flying:
                self.log( "You can't reach the hole in the ceiling." )
            else:
                spot = self.player.tile.ceilingHole.level.getClearTileAround( self.player.tile.ceilingHole )
                self.player.moveto( spot )
                self.log( "You fly through the hole in the ceiling." )
                self.tookAction( 1 )
        else:
            self.log( "You can't see any way to go up right here." )
    def goDown(self):
        if self.player.tile.name == "stairs down":
            nextLev = self.player.tile.level.generateDeeperLevel()
            spot = nextLev.getPlayerSpawnSpot()
            self.player.moveto( spot )
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
                self.player.moveto( spot )
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
            item = self.player.inventory.pop()
            self.player.tile.items.append( item )
            self.log( "You drop %s." % item.name.definiteSingular() )
            self.tookAction( 1 )
    def equipWeapon(self, weapon):
        assert weapon.itemType == 'weapon'
        if self.player.weapon:
            self.player.inventory.append( self.player.weapon )
        self.player.weapon = weapon
        self.log( "You wield %s." % weapon.name.definiteSingular() )
    def accessInventory(self):
        stacked = countItems( self.player.inventory )
        chosen = self.main.query( SelectionMenuWidget, choices = [
            (items[0], name.amount( len(items), informal = True )) for name, items in stacked.items()
        ] + [ (None, "cancel") ], padding = 5 )
        if chosen:
            if chosen.itemType == 'weapon':
                self.equipWeapon( chosen )
            elif chosen.itemType == 'talisman':
                self.log( "You merely need to carry %s for its magics to work." % chosen.name.definiteSingular() )
            elif chosen.itemType == 'rune':
                self.log( "The rune is useless on its own. (Press 'w' to combine runes into spells.)" )
            else:
                self.log( "You don't see how you could maek use of %s." % chosen.name.definiteSingular() )
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
            # TODO replace with hotkey menu
            chosen = self.main.query( SelectionMenuWidget, choices = [
                (spell,"%c: %s (%d)" % (spell.hotkey,spell.name,spell.cost())) for spell in self.context.player.spellbook
            ] + [ (None, "cancel") ], title = "Which spell do you want to cast?", padding = 5 )
            if chosen:
                if self.context.player.payForSpell( chosen.cost() ):
                    chosen.cast( self.context ) # intransitive spells only at the moment
                    self.tookAction( 1 )
    def keyboard(self, key):
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
        if standardAction:
            self.clearlog()
            standardAction()
        elif key == ':': # Look command
            self.main.query( CursorWidget, self )
        elif key == 'Q':
            self.done = True
        elif key == 'q':
            self.context.save( "test-savefile.gz" )
            self.done = True
        elif key == 'V':
            self.restrictVisionByFov = not self.restrictVisionByFov
        elif key == 'T':
            newLevel = mapFromGenerator( self.context )
            self.player.moveto( newLevel.getPlayerSpawnSpot() )
        elif key == 'N':
            from widgets import TextInputWidget
            import string
            self.name = self.main.query( TextInputWidget, 32, okay = string.letters, query = "Please enter your name: " )
        elif key == 'M':
            self.main.query( SelectionMenuWidget, [
                (1, "Team Cake"),
                (2, "Team Pie"),
                (3, "Team Edward"),
                (4, "Team Jacob"),
                (5, "Team Bella"),
                (6, "Team Buffy"),
            ], title = "Choose your team", padding = 5)
        elif key == 'D':
            self.player.trapDetection += 1
        elif key == 'S':
            self.context.save( "test-savefile.gz" )
        elif key == 'C':
            self.showExplosion( (self.player.tile.x, self.player.tile.y), 5 )
        elif key == 'X':
            self.main.query( CursorWidget, self )
    def showEffects(self, effects, t = 0.05):
        fov = self.player.fov( setRemembered = True )
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
    def showStraightRay(self, origin, direction, radius, fg, bg, stopper = lambda xy : False ):
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
        for i in range( radius ):
            cx += dx
            cy += dy
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
