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

class GameContext:
    def log(self, s):
        try:
            self.game.log( s )
        except AttributeError:
            pass
    

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

if __name__ == '__main__':
    from level import *
    from widgets import *
    from gamewidget import GameWidget
    from timing import Simulator
    from ai import *
    import timing

    context = GameContext()

    level = Map( context, 100, 50 )
    level.doRectangle( makeWall, *innerRectangle( level ) )
    level.doRectangle( makeFloor, *innerRectangle( level, 1 ) )
    level.doRectangle( makeWall, *innerRectangle( level, 20 ) )

    context.sim = Simulator() # might want this to follow level instead?
    context.player = level.spawnMobile( Mobile, "at", "@", fgColour = "green", speed = timing.Speed.Quick, context = context, noSchedule = True )

    for i in range(5):
        level.spawnMobile( Mobile, name = "monster", symbol = "x", fgColour = "red", ai = RandomWalker(), context = context )
    for i in range(5):
        level.spawnMobile( Mobile, name = "monster", symbol = "g", fgColour = "yellow", ai = HugBot(target = context.player, radius = 10), speed = timing.Speed.Quick, context = context )

    for i in range(5):
        level.spawnItem( Item, name = "book", symbol = "[", fgColour = "white" )

    try:
        import cursesui
        main = cursesui.main
    except ImportError:
        import tcodui
        main = tcodui.main
    main( GameWidget, level = level, context = context )
