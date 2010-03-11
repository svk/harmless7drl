from level import Mobile, Rarity
from ai import *
from grammar import *
from timing import Speed

Monsters = []

Nibblefish = Mobile(
    name = Noun( "a", "nibblefish", "nibblefishes" ),
    symbol = "~",
    fgColour = "yellow",
    ai = MeleeSeeker( radius = 10 ),
    speed = Speed.Quick,
    walking = False,
    swimming = True,
    groundhugger = True,
    rarity = Rarity( freq = 0 ), # especially generated for water
    attackVerb = Verb( "bite", "bites" ),
)

lastMon = Mufflon = Mobile(
    name = Noun( "a", "mufflon", "mufflons" ),
    symbol = "m",
    fgColour = "blue",
    ai = MeleeMagicHater( radius = 10, tolerance = 0 ),
    speed = Speed.Normal,
    groundhugger = True,
    rarity = Rarity( freq = 1 ), # especially generated for water
    attackVerb = Verb( "ram", "rams" ),
    attackElaboration = " with its horn",
    meleePower = 3,
)
Monsters.append( lastMon )
