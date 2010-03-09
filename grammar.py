def makeList( l ):
    if not l:
        return "nothing"
    if len( l ) == 1:
        return l[0]
    return ", ".join( l[:-1]) + " and " + l[-1]

def makeCountingList( d ):
    rv = []
    for thing, things in d.items():
        rv.append( thing.amount( len(things) ) )
    return makeList( rv )

def capitalizeFirst( s ):
    return s[0].upper() + s[1:]

SmallNumbers = {
    0 : "zero",
    1 : "one",
    2 : "two",
    3 : "three",
    4 : "four",
    5 : "five",
    6 : "six",
    7 : "seven",
    8 : "eight",
    9 : "nine",
    10 : "ten",
    11 : "eleven",
    12 : "twelve",
    13 : "thirteen",
    14 : "fourteen",
    15 : "fifteen",
    16 : "sixteen",
    17 : "seventeen",
    18 : "eighteen",
    19 : "nineteen",
    20 : "twenty",
}

class Noun:
    def __init__(self, article, singular, plural, the = True):
        self.article = article
        self.singular = singular
        self.plural = plural
        self.the = the
    def indefiniteSingular(self):
        rv = [ self.singular ]
        if self.article:
            rv.insert( 0, self.article )
        return " ".join( rv )
    def amount(self, n, informal = False):
        try:
            m = SmallNumbers[n]
        except KeyError:
            m = "%d" % n
        if informal and n == 1 and self.article:
            m = self.article
        return " ".join( [ m, self.plural if n != 1 else self.singular ] )
    def definite(self):
        if self.the:
            return " ".join( [ "the", self.singular ] )
        return self.singular
    def __str__(self):
        return self.singular
    def __eq__(self, that):
        return self.singular == that.singular
    def __hash__(self):
        return self.singular.__hash__()

class ProperNoun ( Noun ):
    def __init__(self, name ):
        Noun.__init__(self, None, name, "<no plural: %s>" % name, the = False )

if __name__ == '__main__':
    penguin = Noun( "a", "penguin", "penguins" )
    print penguin.indefiniteSingular()
    for i in range(40):
        print penguin.indefiniteAmount( i )
    print penguin.definite()
    percy = ProperNoun( "Percy" )
    print percy.indefiniteSingular()
    for i in range(2):
        print percy.indefiniteAmount( i )
    print percy.definite()
