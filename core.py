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

def savefileName( name ):
    import string
    for ch in name:
        if ch not in string.letters:
            return None
    return "savegame-%s-harmless7drl.gz" % name

def loadOldGame( name ):
    context = GameContext()
    context.levels = []
    filename = savefileName( name )
    return context.load( filename )

def beginNewGame( name, gender, cheat = True ):
    from gamewidget import GameWidget
    from timing import Simulator, Speed
    import timing
    from grammar import Noun, ProperNoun
    import sys
    from level import mapFromGenerator, Mobile, Item
    from widgets import RootMenuWidget
    import ai
    import magic
    
    context = GameContext()
    context.levels = []
    
    # hack up a little new environment for us.
    context.protorunes = magic.generateProtorunes()
    level = mapFromGenerator( context )
    level.depth = 1

    if cheat:
        for rune in context.protorunes: # XXX
            rune.identify()

    context.player = Mobile( level.getPlayerSpawnSpot(),
                             ProperNoun( name, gender ),
                             "@",
                             speed = Speed.Normal,
                             context = context,
                             fgColour = "green",
    )
    context.player.rawname = name
    context.player.weapon = magic.Staff( Noun("an", "apprentice's staff", "apprentice's staves" ),
                                         3,
                                         50,
                                         50 ).spawn() # not a cheat!
    if cheat:
        context.player.spellbook.append( magic.Dig() ) # XXX cheat
        context.player.spellbook.append( magic.LevitateSelf() ) # XXX cheat

    for i in range(5):
        level.spawnMobile( Mobile, name = Noun("a", "monster", "monsters"), symbol = "x", fgColour = "blue", ai = ai.RandomWalker(), context = context )
    for i in range(5):
        level.spawnMobile( Mobile, name = Noun("a", "robot", "robots"), symbol = "g", fgColour = "yellow", ai = ai.TurnerBot(), speed = timing.Speed.Normal, context = context, nonalive = True )
    for i in range(5):
        level.spawnItem( Item, name = Noun("a", "book", "books"), symbol = "[", fgColour = "white" )

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

    context = GameContext()
    context.levels = []

#    from levelgen import GeneratorQueue
#    context.levelGenerator = GeneratorQueue( 2, 100, 100 )
    try:
        try:
            raise IOError()
            context = context.load( "test-savefile.gz" )
        except IOError:
            # hack up a little new environment for us.
            context.protorunes = generateProtorunes()
            level = mapFromGenerator( context )
            level.depth = 1

            for rune in context.protorunes: # XXX
                rune.identify()

            context.player = Mobile( level.getPlayerSpawnSpot(),
                                     ProperNoun( "Atman", "male" ),
                                     "@",
                                     speed = Speed.Normal,
                                     context = context,
                                     fgColour = "green",
            )
            context.player.weapon = Staff( Noun("an", "apprentice's staff", "apprentice's staves" ),
                                           3,
                                           50,
                                           50 ).spawn() # not a cheat!
            context.player.spellbook.append( Dig() ) # XXX cheat
            context.player.spellbook.append( LevitateSelf() ) # XXX cheat

            for i in range(5):
                level.spawnMobile( Mobile, name = Noun("a", "monster", "monsters"), symbol = "x", fgColour = "blue", ai = RandomWalker(), context = context )
            for i in range(5):
                level.spawnMobile( Mobile, name = Noun("a", "robot", "robots"), symbol = "g", fgColour = "yellow", ai = TurnerBot(), speed = timing.Speed.Normal, context = context, nonalive = True )
            for i in range(5):
                level.spawnItem( Item, name = Noun("a", "book", "books"), symbol = "[", fgColour = "white" )
        try:
            import cursesui
            main = cursesui.main
        except ImportError:
            import tcodui
            main = tcodui.main
        main( RootMenuWidget )
    finally:
        print "Thanks for playing!"
        print "Please wait, shutting down...",
        sys.stdout.flush()
#        context.levelGenerator.shutdown()
        print "done."
