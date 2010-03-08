from core import Widget
import string

def blinkphase(n = 2, phaselength = 0.5):
    import time
    return int( (time.time() % (n * phaselength)) / phaselength )
    

class TextInputWidget (Widget):
    def __init__(self, width, okay = string.printable, query = None, acceptEmpty = False):
        Widget.__init__(self)
        self.width = width
        self.okay = okay
        self.data = []
        self.query = query
    def draw(self, ui):
        # primitive, obviously, will get better
        y = 0
        if self.query:
            ui.putString( 0, y, self.query )
            y += 1
        ui.putString( 0, y, "".join( self.data ) )
        if blinkphase(2) == 0:
            ui.put( len( self.data ), y, "_" )
    def keyboard(self, key):
        if key == '\n':
            if self.data:
                self.done = True
                self.result = "".join( self.data )
        elif not self.done:
            if key in self.okay:
                if len( self.data ) < self.width:
                    self.data.append( key )
