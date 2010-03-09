from core import Widget
import string

def blinkphase(n = 2, phaselength = 0.5):
    import time
    return int( (time.time() % (n * phaselength)) / phaselength )

PrimaryColour = 'white'
SecondaryColour = 'blue'

class ClippedException: pass

class Subwindow:
    def __init__(self, ui, x0, y0, w, h):
        self.ui = ui
        self.x0, self.y0 = x0, y0
        self.w, self.h = w, h
    def transform(self, x, y):
        if x < 0 or y < 0 or x >= self.w or y >= self.h:
            raise ClippedException()
        x, y = x + self.x0, y + self.y0
        return x,y
    def put(self, x, y, *args, **kwargs):
        try:
            x, y = self.transform(x, y)
            self.ui.put( x, y, *args, **kwargs )
        except ClippedException:
            pass
    def putString(self, x, y, s, *args, **kwargs):
        for ch in s:
            self.put( x, y, ch, *args, **kwargs)
            x += 1
    def decorate(self, borderColour, insideColour):
        for x in range( self.w ):
            for y in range( self.h ):
                col = insideColour
                if x == 0 or y == 0 or x+1 == self.w or y+1 == self.h:
                    col = borderColour
                self.put( x, y, ' ', col, col )

def centeredSubwindow( ui, w, h ):
    wid, hei = ui.dimensions()
    x0 = int( (wid-w) / 2 + 0.5 )
    y0 = int( (hei-h) / 2 + 0.5 )
    x0 = max( 0, x0 )
    y0 = max( 0, y0 )
    w = min( w, wid - x0 )
    h = min( h, hei - y0 )
    return Subwindow( ui, x0, y0, w, h )

class HitEnterWidget (Widget):
    def __init__(self, *args, **kwargs):
        Widget.__init__(self, *args, **kwargs)
    def keyboard(self, key):
        if key == '\n' or key == ' ':
            self.done = True

class TextInputWidget (Widget):
    def __init__(self, width, okay = string.printable, query = None, acceptEmpty = False, *args, **kwargs):
        Widget.__init__(self, *args, **kwargs)
        self.width = width
        self.okay = list( okay )
        self.data = []
        self.query = query
        self.height = 4
        self.resize()
    def resize(self, w = None, h = None):
        self.dialog = centeredSubwindow( self.ui, self.width + 3, self.height )
    def draw(self):
        bg = PrimaryColour
        fg = SecondaryColour
        self.dialog.decorate( fg, bg )
        y = 1
        if self.query:
            self.dialog.putString( 1, y, self.query, fg, bg )
            y += 1
        self.dialog.putString( 1, y, "".join( self.data ), fg, bg )
        if blinkphase(2) == 0:
            self.dialog.put( 1 + len( self.data ), y, "_", fg, bg )
    def keyboard(self, key):
        if key == '\n':
            if self.data:
                self.done = True
                self.result = "".join( self.data )
        elif not self.done:
            if key == 'backspace':
                if self.data:
                    self.data.pop()
            elif key in self.okay:
                if len( self.data ) < self.width:
                    self.data.append( key )

class SelectionMenuWidget (Widget):
    def __init__(self, choices = [], title = None, padding = 0, *args, **kwargs):
        Widget.__init__(self, *args, **kwargs)
        self.title = title
        self.choices = choices # symbol, description
        self.selection = 0
        self.width = max( map( lambda syde : len(syde[1]), self.choices ) )
        self.xoffset = 2
        if self.title:
            self.yoffset = 2
            self.width = max( len(self.title), self.width )
        else:
            self.yoffset = 1
        self.width += self.xoffset + 1
        self.width += padding
        self.height = len( self.choices ) + 1 + self.yoffset
        self.resize()
    def resize(self, w = None, h = None):
        self.dialog = centeredSubwindow( self.ui, self.width, self.height )
    def keyboard(self, key):
        if key == 'north':
            self.selection = max( 0, self.selection - 1 )
        elif key == 'south':
            self.selection = min( len(self.choices) - 1, self.selection + 1 )
        elif key == '\n':
            sym, desc = self.choices[ self.selection ]
            self.result = sym
            self.done = True
    def draw(self):
        bg = PrimaryColour
        fg = SecondaryColour
        self.dialog.decorate( fg, bg )
        i = 0
        if self.width:
            self.dialog.putString( 1, 1, self.title.center( self.width - 2 ), fg, bg )
        for sym, desc in self.choices:
            bga, fga = bg, fg
            if i == self.selection:
                bga, fga = fg, bg
            self.dialog.putString( self.xoffset, i + self.yoffset, desc, fga, bga )
            i += 1
