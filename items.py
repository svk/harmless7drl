import magic
from grammar import Noun, ProperNoun
from level import Rarity, Item

Items = []

lastItem = CrookedStaff = magic.Staff(
    Noun('a', 'crooked staff', 'crooked staves'),
    damage = 2,
    minMana = 50,
    maxMana = 100,
    weight = 10,
    rarity = Rarity( worth = 20, freq = 1, minLevel = 2 )
)
Items.append( lastItem )

lastItem = Tome = magic.Tome(
    Noun( "a", "scroll of magic", "scrolls of magic" ),
    rarity = Rarity( worth = 10,freq = 1 )
)
Items.append( lastItem )

lastItem = Tome = magic.TrapTalisman(
    Noun( "a", "talisman of perception", "talismans of perception" ),
    weight = 5,
    rarity = Rarity( freq = 2, worth = 10 )
)
Items.append( lastItem )

lastItem = HealthTalisman = magic.HealthTalisman(
    Noun( "a", "talisman of health", "talismans of health" ),
    weight = 5,
    rarity = Rarity(worth = 20, freq = 1 , minLevel = 5)
)
Items.append( lastItem )

lastItem = Treasure = magic.Treasure(
    Noun( "a", "heavy spellbook", "heavy spellbooks" ),
    weight = 10,
    rarity = Rarity(worth = 10, freq = 1)
)
Items.append( lastItem )

lastItem = HealPotion = Item(
        # restores a single HP -- you're meant to use magic.
    Noun( "a", "vial of healing essences", "vials of healing essences" ),
    '!',
    'magenta',
    itemType = "healing",
    weight = 5,
    rarity = Rarity( worth = 8, freq = 4 ),
)
Items.append( lastItem )

lastItem = MacGuffinMale = Item(
        # restores a single HP -- you're meant to use magic.
    ProperNoun( "Professor Nislakh", "male" ),
    'h',
    'black',
    itemType = "macguffin",
    weight = 30, # mcg + n heavy books should be full capacity (no staff etc.) - might be a nice challenge for completists
    rarity = Rarity( freq = 0 ), # should be freq 0! unique, generated when you bump into Nislakh.
    isMacGuffin = True,
)

lastItem = MacGuffinFemale = Item(
        # restores a single HP -- you're meant to use magic.
    ProperNoun( "Professor Nislene", "female" ),
    'h',
    'black',
    itemType = "macguffin",
    weight = 30, # mcg + n heavy books should be full capacity (no staff etc.) - might be a nice challenge for completists
    rarity = Rarity( freq = 0 ), # should be freq 0! unique, generated when you bump into Nislakh.
    isMacGuffin = True,
)


if __name__ == '__main__':
    from level import DungeonDepth

    for protorune in magic.generateProtorunes():
        protorune.identify()
        Items.append( protorune )

    for dlevel in range(1,DungeonDepth+1):
        items = [ item for item in Items if item.rarity.eligible( dlevel ) ]
        totalWeight = sum( map( lambda item : item.rarity.frequency, items ) )
        print "Dungeon level %d: %d items" % (dlevel, len(items))
        for item in items:
            print "\t%.2lf%%: %s" % (item.rarity.frequency * 100.0 / totalWeight, item.name.plural)
        print
