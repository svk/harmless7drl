from harmless7drl import Widget
import string
import time
from textwrap import TextWrapper
import sys

MovementKeys = { # authoritative in gamewidget.py
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

def blinkphase(n = 2, phaselength = 0.5):
    import time
    return int( (time.time() % (n * phaselength)) / phaselength )

from harmless7drl import getCfg

prettymenu = getCfg( "tcod", "prettymenu" ) == "yes"
if prettymenu:
    PrimaryColour = 'tcod-primary'
    SecondaryColour = 'tcod-secondary'
    BorderColour = 'tcod-border'
    HighlightPrimaryColour = 'tcod-primary-hl'
    HighlightSecondaryColour = 'tcod-secondary-hl'
else:
    PrimaryColour = 'white'
    SecondaryColour = 'blue'
    BorderColour = SecondaryColour
    HighlightPrimaryColour, HighlightSecondaryColour = SecondaryColour, PrimaryColour

PrimaryColourRGB = 158, 0, 156
BorderColourRGB = 106, 0, 105
SecondaryColourRGB = 182,151,91
HighlightPrimaryColourRGB = PrimaryColourRGB
HighlightSecondaryColourRGB = 255, 255, 255

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
        return x
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

class DelayWidget (Widget):
    def __init__(self, dt = 0.1, *args, **kwargs):
        Widget.__init__(self, *args, **kwargs)
        self.t = time.time() + dt
    def draw(self):
        if time.time() >= self.t:
            self.done = True
        

class DirectionWidget (Widget):
    def __init__(self, acceptZ = False, *args, **kwargs):
        Widget.__init__(self, *args, **kwargs)
        self.movementKeys = MovementKeys
        self.acceptZ = acceptZ
    def keyboard(self, key):
        try:
            self.result = self.movementKeys[key]
            self.done = True
        except KeyError:
            if key == '>' or key == '<' and self.acceptZ:
                self.result = key
                self.done = True

class HitEnterWidget (Widget):
    def __init__(self, *args, **kwargs):
        Widget.__init__(self, *args, **kwargs)
    def keyboard(self, key):
        if key == '\n' or key == ' ':
            self.done = True

class TextInputWidget (Widget):
    def __init__(self, width, okay = string.printable, query = None, acceptEmpty = False, centered = False, *args, **kwargs):
        Widget.__init__(self, *args, **kwargs)
        self.width = width
        self.okay = list( okay )
        self.data = []
        self.query = query
        self.centered = centered
        self.height = 4
        self.resize()
    def resize(self, w = None, h = None):
        self.dialog = centeredSubwindow( self.ui, self.width + 3, self.height )
    def draw(self):
        bg = PrimaryColour
        fg = SecondaryColour
        self.dialog.decorate( BorderColour, bg )
        y = 1
        if self.query:
            x = self.dialog.putString( 1, y, self.query.center( self.width + 1 ) if self.centered else self.query, fg, bg )
            y += 1
        x = 1
        if self.centered:
            x = int( (self.width + 3 - len(self.data)) / 2 )
        x = self.dialog.putString( x, y, "".join( self.data ), fg, bg )
        if blinkphase(2) == 0:
            self.dialog.put( x, y, "_", fg, bg )
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

class WallOfTextWidget (HitEnterWidget):
    def __init__(self, text, width, center = False, *args, **kwargs):
        HitEnterWidget.__init__(self, *args, **kwargs)
        self.width = width
        self.center = center
        self.text = text
    def draw(self):
        bg = PrimaryColour
        fg = SecondaryColour
        screenw, screenh = self.ui.dimensions()
        tw = TextWrapper( self.width - 2 )
        tw.feed( self.text )
        height = min( tw.numberOfLines() + 2, screenh )
        dialog = centeredSubwindow( self.ui, self.width, height )
        dialog.decorate( BorderColour, bg )
        i = 0
        for i in range(1, height-1):
            s = tw.line(i-1)
            if self.center:
                s = s.center( self.width - 2 )
            dialog.putString( 1, i, s, fg, bg )
        

class CursorWidget (Widget):
    def __init__(self, game, *args, **kwargs):
        Widget.__init__(self, *args, **kwargs)
        self.game = game
        self.game.cursor = self.game.player.tile.x, self.game.player.tile.y
        self.visibility = game.playerVisibility( game.player.fov() )
        self.description = ""
    def draw(self):
        screenw, screenh = self.game.ui.dimensions()
        tw = TextWrapper( screenw, self.game.textfieldheight )
        tw.feed( self.description )
        if tw.pages:
            page = tw.popPage()
        else:
            lines = [ tw.line(0), tw.line(1) ]
        for i in range(2):
            try:
                self.game.ui.putString( 0, i, " " * screenw, 'bold-white' )
                self.game.ui.putString( 0, i, lines[i], 'bold-white' )
            except IndexError:
                pass
    def keyboard(self, key):
        try:
            dx, dy = MovementKeys[ key ]
            x, y = self.game.cursor
            self.game.cursor = x+dx,y+dy
            try:
                tile = self.game.player.tile.level.tiles[ self.game.cursor ]
            except KeyError:
                tile = None
            if tile and self.visibility( tile ):
                self.description = self.game.player.tile.level.tiles[ self.game.cursor ].describe()
            else:
                self.description = ""
                try:
                    if self.game.player.tile.level.tiles[ self.game.cursor ].rememberedAs:
                        self.description = self.game.player.tile.level.tiles[ self.game.cursor ].describeRemembered()
                except IndexError:
                    pass
        except KeyError:
            if key == '\n' or key == ' ':
                self.result = self.game.cursor
                self.game.cursor = None
                self.done = True

class SelectionMenuWidget (Widget):
    def __init__(self, choices = [], title = None, centered = False, noInvert = False, padding = 0, *args, **kwargs):
        Widget.__init__(self, *args, **kwargs)
        self.title = title
        self.choices = choices # symbol, description
        self.selection = 0
        self.noInvert = noInvert
        self.width = max( map( lambda syde : len(syde[1]) + 2 + 2, self.choices ) )
        self.centered = centered
        self.xoffset = 2 if not self.centered else 1
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
        if key == '\n':
            sym, desc = self.choices[ self.selection ]
            self.result = sym
            self.done = True
        else:
            try:
                translated = MovementKeys[key]
                if translated == (0,-1):
                    self.selection = max( 0, self.selection - 1 )
                elif translated == (0,1):
                    self.selection = min( len(self.choices) - 1, self.selection + 1 )
            except KeyError:
                pass
    def draw(self):
        bg = PrimaryColour
        fg = SecondaryColour
        self.dialog.decorate( BorderColour, bg )
        i = 0
        if self.title:
            self.dialog.putString( 1, 1, self.title.center( self.width - 2 ), fg, bg )
        for sym, desc in self.choices:
            bga, fga = bg, fg
            if i == self.selection:
                if not self.noInvert:
                    bga = HighlightPrimaryColour
                    fga = HighlightSecondaryColour
                desc = " ".join( [ ">", desc, "<" ] )
            if self.centered:
                desc = desc.center( self.width - 2)
            self.dialog.putString( self.xoffset, i + self.yoffset, desc, fga, bga )
            i += 1

class SpellSelectionMenuWidget (SelectionMenuWidget):
    def __init__(self, hotkeys = {}, *args, **kwargs):
        SelectionMenuWidget.__init__(self, *args, **kwargs)
        self.hotkeys = hotkeys
    def keyboard(self, key):
        try:
            self.result = self.hotkeys[key]
            self.done = True
        except KeyError:
            SelectionMenuWidget.keyboard( self, key )


class RootMenuWidget(Widget):
    def __init__(self, *args, **kwargs):
        Widget.__init__(self, *args, **kwargs)
    def draw(self):
        # display a splash screen
        from harmless7drl import Signature, Version, Date, Author, Email
        lines = [ Signature, Version, Date, "", "by %s" % Author, Email, "", "For the 2010 7DRL challenge", "", "Press any key to continue" ]
        screenw, screenh = self.ui.dimensions()
        y = ( screenh-len(lines) ) // 2 
        for line in lines[:-1]:
            self.ui.putString( 0, y, line.center( screenw ), "bold-white", "black" )
            y += 1
        self.ui.putString( 0, y, lines[-1].center( screenw ), "bold-white", "black" )
    def keyboard(self, key):
        from gamewidget import GameWidget
        self.hidden = True # remember: that's the _splash_ screen
        while True:
            result = self.main.query( SelectionMenuWidget, choices = [
                ('new', "Play Harmless7DRL"),
                ('instructions', "Instructions"),
                ('about', "About"),
                ('quit', "Quit"),
            ], padding = 5, centered = True, noInvert = True )
            if result == 'quit':
                self.done = True
                break
            elif result == 'new':
                self.main.query( GameWidget )
            elif result == 'instructions':
                from plot import displayInstructions
                displayInstructions( self.main )
            elif result == 'about':
                from plot import displayAbout
                displayAbout( self.main )
