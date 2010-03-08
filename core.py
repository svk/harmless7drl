class Widget:
    def __init__(self):
        self.done = False
        self.result = None
        self.hidden = False
    def focus(self):
        pass
    def draw(self, ui):
        pass
    def keyboard(self, key):
        pass
    def resized(self, screenwidth, screenheight):
        pass

class ResizedException:
    pass

class MainLoop:
    def __init__(self, ui):
        self.widgets = []
        self.ui = ui
    def draw(self):
        self.ui.clear()
        for widget in self.widgets:
            if not widget.hidden:
                widget.draw( self.ui )
        self.ui.show()
    def resize(self):
        w, h = self.ui.dimensions()
        for widget in self.widgets:
            widget.resized( w, h )
    def query(self, widget, *args, **kwargs):
        w = widget( *args, **kwargs )
        w.main = self
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
    class HelloWorldWidget ( Widget ):
        def __init__(self):
            Widget.__init__( self )
            self.lastKey = None
            self.name = None
        def draw(self, ui):
            import time
            ui.putString( 10, 10, "Hello world!" )
            ui.putString( 10, 11, "Time: %lf" % time.time() )
            ui.putString( 10, 12, "Last keypress: %s" % self.lastKey )
            ui.putString( 10, 13, "Your name: %s" % self.name )
        def keyboard(self, key):
            if key == 'q':
                self.done = True
            if key == 'N':
                from widgets import TextInputWidget
                import string
                self.name = self.main.query( TextInputWidget, 32, okay = string.letters, query = "Please enter your name: " )
            self.lastKey = key

    from cursesui import CursesInterface, handleException
    try:
        cui = CursesInterface()
        main = MainLoop( cui )
        main.query( HelloWorldWidget )
    except:
        handleException()
