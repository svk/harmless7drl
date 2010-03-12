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
    ai = MeleeMagicHater( radius = 5, tolerance = 0 ),
    speed = Speed.Normal,
    groundhugger = True,
    rarity = Rarity( freq = 1 ),
    attackVerb = Verb( "ram", "rams" ),
    attackElaboration = " with its horn",
    meleePower = 3, # very powerful melee, incentive to stay away
    hitpoints = 10,
)
Monsters.append( lastMon )

lastMon = Rook = Mobile(
    name = Noun( "a", "rook", "rooks" ),
    symbol = "R",
    fgColour = "white",
    ai = Rook( radius = 8 ), # just for testing, should be 8
    speed = Speed.Normal, # actually moves several tiles in a turn, though.
    rarity = Rarity( freq = 1 ),
    attackVerb = Verb( "slam into", "slams into" ),
    meleePower = 3, # another don't-get-hit puzzle
    hitpoints = 1, # it's easy to capture a chess piece..
)
Monsters.append( lastMon )

Boulder = Mobile(
    name = Noun( "a", "boulder", "boulders" ),
    symbol = "0",
    fgColour = "white",
    ai = BoulderAi(),
    rarity = Rarity( freq = 0 ),
    hitpoints = 400,
    nonalive = True,
    destroyedByDigging = True,
    pushable = True,
)

lastMon = Imp = Mobile(
    name = Noun( "an", "imp", "imps", gender = 'random' ),
    symbol = "i",
    fgColour = "magenta",
    ai = DebufferAi( radius = 8 ),
    speed = Speed.VeryQuick,
    rarity = Rarity( freq = 1 ),
    hitpoints = 5,
    flying = True,
)
Monsters.append( lastMon )

lastMon = Gnome = Mobile(
    name = Noun( "a", "gnome", "gnomes", gender = 'random' ),
    symbol = "g",
    fgColour = "blue",
    ai = StaffStealer( radius = 8 ),
    speed = Speed.Normal,
    groundhugger = True,
    rarity = Rarity( freq = 10 ),
    hitpoints = 5,
)
Monsters.append( lastMon )

