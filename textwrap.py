import string

# Should support spaces, newlines, tabs (= 4 spaces don't glob at beginning of line)

class TextWrapper:
    def __init__(self, width):
        self.width = width
        self.lines = []
        self.lastline = []
        self.breakAt = None
        self.tabbing = 0
    def lastlinelength(self):
        return len( "".join( self.lastline ) )
    def centeredline(self, i):
        l = self.line( i )
        if l:
            return l.center( self.width )
        return None
    def haslastline(self):
        if not self.lastline:
            return False
        return not "".join( self.lastline ).isspace()
    def line(self, i):
        try:
            return self.lines[i]
        except IndexError:
            if len( self.lines ) == i:
                return "".join( self.lastline )
            return ""
    def height(self):
        rv = len( self.lines )
        if self.haslastline():
            rv += 1
        return rv
    def feed(self, s):
        for ch in s:
            self.feedChar( ch )
    def feedChar(self, ch):
        accept = None
        if ch == ' ':
            self.breakAt = len( self.lastline )
            accept = " "
        elif ch == '\n':
            self.lines.append( "".join( self.lastline ) )
            self.lastline = []
            self.tabbing = 0
        elif ch == '\t':
            if not self.lastline:
                accept = "    "
            self.tabbing += 4
        else:
            accept = ch
        if accept:
            if self.lastlinelength() + len( accept ) > self.width:
                newline = [ " " * self.tabbing ]
                if not self.breakAt:
                    self.lines.append( "".join( self.lastline ) )
                else:
                    self.lines.append( "".join( self.lastline[:self.breakAt] ) )
                    newline.append( "".join(self.lastline[self.breakAt+1:]) )
                if not accept.isspace():
                    newline.append( accept )
                self.lastline = newline
                self.breakAt = None
            else:
                self.lastline.append( accept )

if __name__ == '__main__':
    w = 40
    wr = TextWrapper( w )

    for i in range(4):
        wr.feed( "0123456789" )

    wr.feed( "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Ut in mi leo. In hac habitasse platea dictumst. Suspendisse arcu orci, viverra ac pretium in, condimentum nec nunc. Nulla massa velit, commodo sit amet venenatis at, tempor ut leo. Suspendisse sollicitudin vulputate lectus et consequat. Etiam dui nulla, blandit et congue sed, rutrum non ante. Fusce non auctor nibh. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Nam hendrerit ornare sapien, eget commodo urna mollis pulvinar. Pellentesque ullamcorper sem ut leo feugiat a volutpat justo elementum. Etiam nec enim mi. Phasellus cursus eros at diam viverra hendrerit. Fusce accumsan magna pellentesque lacus malesuada porttitor.\n\n" )
    wr.feed( "\tFusce ac nulla sit amet erat luctus sagittis. Duis lobortis condimentum risus, congue luctus justo ultricies non. Fusce et metus quis purus venenatis molestie quis vitae tellus. In molestie, mi eget elementum luctus, neque arcu vehicula lorem, ut rutrum sem arcu et lectus. Integer lacinia lacinia tortor, ut bibendum quam hendrerit sed. Aenean interdum, leo et accumsan mollis, ante nulla tristique mauris, sed porta lacus arcu tempor magna. Aliquam erat volutpat. Fusce leo felis, adipiscing id dictum ac, convallis eu dolor. Aenean tempor sapien magna. Etiam accumsan ipsum at arcu consectetur egestas. Maecenas tortor nibh, tempus in viverra vel, volutpat vitae eros. Sed convallis augue ac nisi consequat eget egestas erat placerat. Curabitur nec lacus auctor diam lobortis pulvinar. Aliquam porta imperdiet ornare.\n\n" )
    wr.feed( "Hi mom!\n" )

    for i in range( wr.height() ):
        l = wr.line(i)
        print l.ljust( w, '.' )
