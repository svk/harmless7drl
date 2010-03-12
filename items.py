import magic
from grammar import Noun
from level import Rarity

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

if __name__ == '__main__':
    dungeonDepth = 10

    for protorune in magic.generateProtorunes():
        protorune.identify()
        Items.append( protorune )

    for dlevel in range(1,dungeonDepth+1):
        items = [ item for item in Items if item.rarity.eligible( dlevel ) ]
        totalWeight = sum( map( lambda item : item.rarity.frequency, items ) )
        print "Dungeon level %d: %d items" % (dlevel, len(items))
        for item in items:
            print "\t%.2lf%%: %s" % (item.rarity.frequency * 100.0 / totalWeight, item.name.plural)
        print
