import copy

Signature = "Harmless7DRL"
Version = "Version 1.1"
Author = "kaw"
Date = "?"
Email = "kaw.dev@gmail.com"

from ConfigParser import RawConfigParser, NoOptionError
Cfg = RawConfigParser()
Cfg.read( "harmless7drl.cfg" )

def getCfg( section, setting, default = None ):
    try:
        return Cfg.get( section, setting )
    except NoOptionError:
        return default

ForegroundBlack = getCfg( "colours", "blackOnBlack", "black" )
DebugMode = getCfg( "general", "debug", "no" ) == "yes"
RootMode = getCfg( "general", "writedir", "gamedir" )

class Widget:
    def __init__(self, main = None, ui = None):
        self.done = False
        self.result = None
        self.hidden = False
        self.main = main
        self.ui = ui
    def focus(self):
        pass
    def draw(self):
        pass
    def keyboard(self, key):
        pass
    def resized(self, screenwidth, screenheight):
        pass

class ResizedException:
    pass

from serialization import GameContext

class MainLoop:
    def __init__(self, ui):
        self.widgets = []
        self.ui = ui
    def draw(self):
        self.ui.clear()
        for widget in self.widgets:
            if not widget.hidden:
                widget.draw()
        self.ui.show()
    def resize(self):
        w, h = self.ui.dimensions()
        for widget in self.widgets:
            widget.resized( w, h )
    def query(self, widget, *args, **kwargs):
        w = widget( ui = self.ui, main = self, *args, **kwargs )
        self.widgets.append( w )
        while not w.done:
            self.draw()
            rv = None
            try:
                rv = self.ui.get()
            except ResizedException:
                self.resize()
            if rv:
                if rv.type == "keypress":
                    w.keyboard( rv.key )
        wp = self.widgets.pop()
        assert w == wp
        if self.widgets:
            self.widgets[-1].focus()
        return w.result

def windowsGetRoot():
    # Using a separate dir to write to means that people can install to
    # "Program Files" without Vista complaining at them. (_Unless_
    # they want to modify the config file, but that's on them, honestly.)
    import os
    appdata = os.environ['APPDATA']
    drive, head = os.path.splitdrive( appdata )
    comps = []
    while head:
        head, tail = os.path.split( tail )
        if tail:
            comps.append( tail )
    comps.reverse()
    comps.append( "Harmless7DRL" )
    return drive + "/".join( comps )
    
def getRoot():
    return {
        'gamedir' : lambda : '.',
        'linuxtemp': lambda : '/tmp/harmless7drl-data', # really just for testing!
        'win32appdata': windowsGetRoot,
    }[ RootMode ]()

def ensureDirPresent( dirname ):
    import os
    fulldirname = "/".join( [getRoot(), dirname] )
    if os.path.exists( fulldirname ):
        return
    os.makedirs( fulldirname )

def fullFilename( dirname, filename ):
    return "/".join( [ getRoot(), dirname, filename ] )

def savefileName( name ):
    import string
    ensureDirPresent( "savegame" )
    for ch in name:
        if ch not in string.letters:
            return None
    return fullFilename( "savegame", "savegame-%s-harmless7drl.gz" % name )

def loadOldGame( name ):
    context = GameContext()
    context.levels = []
    filename = savefileName( name )
    rv = context.load( filename )
    import os
    os.unlink( filename )
    return rv

def beginNewGame( context, name, gender, cheat = True ):
    from gamewidget import GameWidget
    from timing import Simulator, Speed
    import timing
    from grammar import Noun, ProperNoun
    import sys
    from level import mapFromGenerator, Mobile, Item, Rarity
    from widgets import RootMenuWidget
    import ai
    import magic
    from monsters import Monsters
    from items import Items
    
    context.levels = []
    
    # hack up a little new environment for us.
    context.protorunes = magic.generateProtorunes()

    context.protoitems = context.protorunes + Items

    context.protomonsters = copy.copy( Monsters )

    level = mapFromGenerator( context )
    level.depth = 1

    context.player = Mobile( 
                             ProperNoun( name, gender ),
                             "@",
                             speed = Speed.Normal,
                             context = context,
                             fgColour = "green",
                             proto = False,
                             tile = level.getPlayerSpawnSpot(),
                             rarity = Rarity( freq = 0 ),
                             walking = True,
                             swimming = True,
    )
    context.player.rawname = name
    context.player.weapon = magic.Staff( Noun("an", "apprentice's staff", "apprentice's staves" ),
                                         3,
                                         50,
                                         50,
                                         weight = 10,
                                         rarity = Rarity( freq = 0) # dummy value, never spawned
                                        ).spawn() # not a cheat!
#    for i in range(5):
#        level.spawnMobile( Mobile, name = Noun("a", "monster", "monsters"), symbol = "x", fgColour = "blue", ai = ai.RandomWalker(), context = context )
#    for i in range(5):
#        level.spawnMobile( Mobile, name = Noun("a", "robot", "robots"), symbol = "g", fgColour = "yellow", ai = ai.TurnerBot(), speed = timing.Speed.Normal, context = context, nonalive = True )
#    for i in range(5):
#        level.spawnItem( Item, weight = 1, name = Noun("a", "book", "books"), symbol = "[", fgColour = "white", rarity = 1k )

    return context

    


if __name__ == '__main__':
    from level import *
    from widgets import *
    from gamewidget import GameWidget
    from timing import Simulator
    from ai import *
    import timing
    from grammar import Noun, ProperNoun
    import sys
    from magic import *
    import serialization

    context = GameContext()
    context.levels = []
    serialization.initializeSerialization()

#    from levelgen import GeneratorQueue
#    context.levelGenerator = GeneratorQueue( 2, 100, 100 )
    try:
        try:
            import cursesui
            main = cursesui.main
        except ImportError:
            import tcodui
            main = tcodui.main
        main( RootMenuWidget )
    finally:
        print "Thanks for playing!"
