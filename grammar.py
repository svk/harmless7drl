import random

def makeList( l ):
    if not l:
        return "nothing"
    if len( l ) == 1:
        return l[0]
    return ", ".join( l[:-1]) + " and " + l[-1]

def makeCountingList( d ):
    rv = []
    for thing, things in d.items():
        rv.append( thing.amount( len(things), informal = True ) )
    return makeList( rv )

def capitalizeFirst( s ):
    if not s:
        return ""
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

def NumberWord( n ):
    try:
        m = SmallNumbers[n]
    except KeyError:
        m = "%d" % n

class Verb:
    def __init__(self, person2, person3 = None): # plural or first-person is not really needed
        self.person2 = person2
        if not person3:
            person3 = person2 + "s"
        self.person3 = person3
    def second(self):
        return self.person2
    def third(self):
        return self.person3

class Noun:
    def __init__(self, article, singular, plural, gender = "neuter", the = True):
        self.article = article
        self.singular = singular
        self.plural = plural
        self.the = the
        self.gender = gender
    def absorb(self, that):
        self.article = that.article
        self.singular = that.singular
        self.plural = that.plural
        self.the = that.the
        self.gender = that.gender
    def pronounPossessive(self):
        if self.gender == "female":
            return "her"
        if self.gender == "male":
            return "his"
        return "its"
    def pronounReflexive(self):
        if self.gender == "female":
            return "herself"
        if self.gender == "male":
            return "himself"
        return "itself"
    def pronounObject(self):
        if self.gender == "female":
            return "her"
        if self.gender == "male":
            return "him"
        return "it"
    def pronounSubject(self):
        if self.gender == "female":
            return "she"
        if self.gender == "male":
            return "he"
        return "it"
    def indefiniteSingular(self):
        rv = [ self.singular ]
        if self.article:
            rv.insert( 0, self.article )
        return " ".join( rv )
    def amount(self, n, informal = False):
        m = NumberWord( n )
        if informal and n == 1 and self.article:
            m = self.article
        return " ".join( [ m, self.plural if n != 1 else self.singular ] )
    def definiteSingular(self):
        if self.the:
            return " ".join( [ "the", self.singular ] )
        return self.singular
    def __str__(self):
        return self.singular
    def __eq__(self, that):
        return self.singular == that.singular
    def __hash__(self):
        return self.singular.__hash__()
    def selectGender(self):
        if self.gender != 'random':
            return self
        import copy
        rv = copy.copy( self )
        rv.gender = 'male' if random.randint(0,1) else 'female'
        return rv

class ProperNoun ( Noun ):
    def __init__(self, name, gender ):
        Noun.__init__(self, None, name, "<no plural: %s>" % name, the = False, gender = gender )
    def amount(self, n, informal = False):
        if n == 1:
            return self.singular
        return Noun.amount(self, n, informal = informal)

if __name__ == '__main__':
    penguin = Noun( "a", "penguin", "penguins" )
    print penguin.indefiniteSingular()
    for i in range(40):
        print penguin.indefiniteAmount( i )
    print penguin.definiteSingular()
    percy = ProperNoun( "Percy" )
    print percy.indefiniteSingular()
    for i in range(2):
        print percy.indefiniteAmount( i )
    print percy.definiteSingular()
