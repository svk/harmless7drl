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
    symbol = "M",
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
    rarity = Rarity( freq = 1000 ),
    attackVerb = Verb( "slam into", "slams into" ),
    meleePower = 3, # another don't-get-hit puzzle
    hitpoints = 1, # it's easy to capture a chess piece..
    chesspiece = True,
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
    hindersLOS = True,
    isBoulder = True,
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
    rarity = Rarity( freq = 1 ),
    hitpoints = 5,
)
Monsters.append( lastMon )

lastMon = GiantMole = Mobile(
    name = Noun( "a", "giant mole", "giant moles" ),
    symbol = "m",
    fgColour = "yellow",
    ai = DigAnimal( radius = 8 ),
    speed = Speed.Slow,
    groundhugger = True,
    rarity = Rarity( freq = 1 ),
    hitpoints = 8,
    attackElaboration = " with its claws",
)
Monsters.append( lastMon )

lastMon = BomberBug = Mobile(
    name = Noun( "a", "bomber beetle", "bomber beetles" ),
    symbol = "b",
    fgColour = "black",
    ai = MeleeSeeker( radius = 4 ),
    speed = Speed.Slow,
    groundhugger = True,
    rarity = Rarity( freq = 1 ),
    hitpoints = 1,
    attackVerb = Verb( "bite", "bites" ),
    onDeath = ExplodesOnDeathHook( radius = 5, damage = 1 ), # might trigger a chain reaction..
)
Monsters.append( lastMon )

lastMon = Spectre = Mobile(
        # extremely slow, but instakills
        # incorporeal!
    name = Noun( "a", "spectre of death", "spectres of death" ),
    symbol = "S",
    fgColour = "white",
    ai = IncorporealSeeker(),
    speed = Speed.VerySlow,
    rarity = Rarity( freq = 1 ),
    hitpoints = 1000,
    meleePower = 1000,
    incorporeal = True,
    nonalive = True,
    flying = True,
    attackVerb = Verb( "touch", "touches" ),
)
Monsters.append( lastMon )

lastMon = Sniffler = Mobile(
        # a cutesy low-level monster that might be less harmless
        # than it appears
    name = Noun( "a", "sniffler", "snifflers" ),
    symbol = "s",
    fgColour = "yellow",
    ai = PlayerTrailFollower(radius = 5), #radius is just for seek if provoked
    speed = Speed.Normal,
    groundhugger = True,
    rarity = Rarity( freq = 100 ),
    hitpoints = 5,
    meleePower = 1,
    attackVerb = Verb( "bite", "bites" ),
)
Monsters.append( lastMon )

if __name__ == '__main__':
    dungeonDepth = 10
    for dlevel in range(1,dungeonDepth+1):
        monsters = [ monster for monster in Monsters if monster.rarity.eligible( dlevel ) ]
        totalWeight = sum( map( lambda monster : monster.rarity.frequency, monsters ) )
        print "Dungeon level %d: %d creatures" % (dlevel, len(monsters))
        for monster in monsters:
            print "\t%.2lf%%: %s" % (monster.rarity.frequency * 100.0 / totalWeight, monster.name.plural)
        print
