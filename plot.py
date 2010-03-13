from widgets import WallOfTextWidget
from grammar import capitalizeFirst, NumberWord
from level import countItems

def convertMacGuffin( mob ):
    if mob.scheduledAction:
        mob.scheduledAction.cancel()
    mob.noSchedule = True
    mob.tile.leaves()
    player = mob.context.player
    item = mob.context.macGuffin
    name = mob.name
    mob.context.log( "%s glares at you angrily and boops ominously." % name.definiteSingular() )
    if item.weight + player.inventoryWeight() > player.weightLimit:
        mob.context.log( "As you shout the code word into what looks like a sound receptor, %s winds down immediately." % name.pronounSubject() )
        mob.context.log( "%s's small enough that you should be able to pick %s up easily." % (name.pronounSubject(), name.pronounObject() ) )
        mob.context.log( "However, %s's too heavy to carry without dropping something else first." % name.pronounSubject() )
        mob.tile.items.append( item )
    else:
        mob.context.log( "As you shout the code word into what looks like a sound receptor, %s winds down immediately, allowing you to pick %s up without much difficulty." % (name.pronounSubject(), name.pronounObject() ))
        player.inventoryGive( item )
    # TODO spawn more monsters on all levels above this one

def displayIntro( game ):
    game.main.query( WallOfTextWidget, width = 60, center = True, text = """\
It had seemed like such an easy job.\
\n
%s %s had appointed you personal assistant to\
 %s, the Special Advisor on Magical Warfare.\
\n
Now,\
 it was widely known that the title of "personal assistant" was a\
 euphemism. Your real job was to make sure %s didn't run\
 away, and that %s did not work any unauthorized magic. %s was a\
 magically animated automaton, a techno-magical wonder left over\
 from the war. Although %s immense intelligence made %s\
 an asset that the University could not afford to lose, as a\
 sentient weapon %s had been programmed to be vicious to the core,\
 and if left to %s own devices %s would surely hatch some\
 insidious plot of mass destruction.""" % (
    game.context.bossTitle,
    game.context.bossName.singular,
    game.context.macGuffin.name.singular,
    game.context.macGuffin.name.pronounSubject(),
    game.context.macGuffin.name.pronounSubject(),
    game.context.macGuffin.name.singular,
    game.context.macGuffin.name.pronounPossessive(),
    game.context.macGuffin.name.pronounObject(),
    game.context.macGuffin.name.pronounSubject(),
    game.context.macGuffin.name.pronounPossessive(),
    game.context.macGuffin.name.pronounSubject(),
))
    game.main.query( WallOfTextWidget, width = 60, center = True, text = """\
Intellectually you were well aware that %s was capable of this.\
 %s'd been responsible for schemes that had cost thousands of\
 lives during the war. But since %s was a\
 cute little clockwork being of no more than sixteen inches,\
 always walked with a ridiculous wobble, and communicated\
 verbally only in beeps and boops, it was, frankly, hard\
 to take %s seriously as a threat to humankind. Besides, the University\
 had managed to reprogram %s to be unable to directly harm a\
 human being in any way, and moreover, to fall asleep for forty-eight\
 hours at the mere sound of the word NIPLOP. With these safeguards,\
 being %s minder ought to be the easiest job in the world.""" % (
    game.context.macGuffin.name.pronounSubject(),
    capitalizeFirst( game.context.macGuffin.name.pronounSubject() ),
    game.context.macGuffin.name.singular,
    game.context.macGuffin.name.pronounObject(),
    game.context.macGuffin.name.pronounObject(),
    game.context.macGuffin.name.pronounPossessive(),
))
    game.main.query( WallOfTextWidget, width = 60, center = True, text = """\
Or so you'd thought.\
\n
Which is why you'd brought a novel with you,\
 to have something to do in between fetching books for the\
 Professor for %s research. During a particularly exciting passage\
 in chapter thirty-six, you'd been rudely interrupted by a loud\
 magical-sounding noise and the disappearance of %s,\
 along with half the library, into a vast magical portal.""" % (
    game.context.macGuffin.name.pronounPossessive(),
    game.context.macGuffin.name.singular,
))
    game.main.query( WallOfTextWidget, width = 60, center = True, text = """\
Now, you consider yourself a lover, not a fighter. But you're a\
 smart, resourceful %s, and you'll have all the resources of the Applied Runic Magic\
 section of the library at your disposal -- if you can only manage to\
 recover them. And all you're up against is a little dungeon and a\
 miniature robot that can't even harm you.\
\n
Hoping that %s will forgive your carelessness if you compensate\
 for it with a little reckless heroism, you jump in after the Professor\
 to retrieve %s.""" % (
    "boy" if game.context.player.name.gender == "male" else "girl",
    game.context.bossName.singular,
    game.context.macGuffin.name.pronounObject(),
))


def displayOutro( game, booksRetrieved ):
    game.main.query( WallOfTextWidget, width = 60, center = True, text = """\
Returning to the University with the Professor slung over your\
 shoulder, you are greeted as a hero by masses of students. As you\
 walk past them to face the %s, University magicians\
 seal the portal behind you.""" % (
    game.context.bossTitle,
))
    if booksRetrieved > 0:
        bookComment = "%s also commends you on bringing back %s of the library's most valuable magical books." % (capitalizeFirst( game.context.bossName.pronounSubject() ), NumberWord( booksRetrieved ) )
    else:
        bookComment = "%s does bemoan the fact that so many of the library's most valuable books were lost." % capitalizeFirst( game.context.bossName.pronounSubject() )
        
    game.main.query( WallOfTextWidget, width = 60, center = True, text = """\
%s chastises you for your recklessness but commends you for\
 your bravery and skill. %s\
\n
%s promises to reward you with a promotion as soon as %s can\
 find a better task for you -- one more suited to your obvious magical talent and less\
 requiring of the exercise of prudence. For the moment, your work\
 as assistant to %s is suspended, as he is confined to a\
 magical holding cell.\
\n
Having saved the day and lived to tell the tale, you breathe\
 a sigh of relief and prepare to do just that.""" % (
    game.context.bossName.singular,
    bookComment,
    capitalizeFirst( game.context.bossName.pronounSubject() ),
    game.context.bossName.pronounSubject(),
    game.context.macGuffin.name.singular,
))
    game.main.query( WallOfTextWidget, width = 60, center = True, text = """\
Congratulations on your victory! A log file has been written to\
 the game directory. (not really yet)""")

def writeReport( game, won, books = 0 ):
    import time
    unfriendlytime = time.strftime( "%Y-%m-%d-%H-%M-%S-%Z" )
    friendlytime = time.strftime( "%d/%m/%Y %H:%M" )
    name = game.player.name.singular
    Psub = capitalizeFirst( game.player.name.pronounSubject() )
    reportName = "harmless7drl-%s-%s.txt" % (name, unfriendlytime )
    f = open( reportName, "w" )
    
    if won:
        print >>f, "%s successfully retrieved the Professor at %s." % (name, friendlytime)
        if books > 0:
            if books == 1:
                print >>f, "%s also returned a valuable books to the library." % (Psub)
            else:
                print >>f, "%s also returned %d valuable books to the library." % (Psub, books)
    else:
        print >>f, "%s perished in the dungeon at %s." % (name, friendlytime)
    print >>f
    
    print >>f, "%s spent %d ticks in the dungeon." % (Psub, game.context.totalTime)
    print >>f, "%s reached dungeon level %d." % (Psub, game.player.greatestDepth )
    print >>f, "%s drained %d points' worth of magical energy from artifacts while in the dungeon." % (Psub, game.player.manaUsed)
    print >>f, "%s had %d/%d hit points." % (Psub, game.player.hitpoints, game.player.maxHitpoints )
    if game.player.weapon:
        print >>f, "%s was wielding %s." % (Psub, game.player.weapon.name.indefiniteSingular() )
    print >>f

    identifiedProtorunes = [ protorune for protorune in game.context.protorunes if protorune.identified ]
    if identifiedProtorunes:
        for protorune in identifiedProtorunes:
            print >>f, "%s had identified the \"%s\" rune as \"%s\"." % (Psub, protorune.arcaneName, protorune.englishName )
    else:
        print >>f, "%s hadn't identified any runes."

    if game.player.inventory:
        print >>f, "%s was carrying:" % Psub
        for name, items in countItems( game.player.inventory ).items():
            print >>f, "\t", name.amount( len(items) )
    else:
        print >>f, "%s was not carrying anything." % Psub
    print >>f

    if game.player.spellbook:
        print >>f, "%s had the following spells in %s spellbook:" % (Psub, game.player.name.pronounPossessive() )
        for spell in game.player.spellbook:
            if spell.castCount == 0:
                x = "(never cast)"
            else:
                if spell.castCount == 1:
                    x = "(cast one time)"
                else:
                    x = "(cast %d times)" % spell.castCount
            print >>f, "\t", spell.name, x
    else:
        print >>f, "%s had no spells in %s spellbook." % (Psub, game.player.name.pronounPossessive() )
    print >>f


    print >>f, "%s encountered the following creatures:" % (Psub)
    for protomonster in game.context.protomonsters:
        if protomonster.spawnCount == 0:
            continue
        x = []
        if protomonster.killCount > 0:
            x.append( "%d perished" % protomonster.killCount )
        if protomonster.directKillCount > 0:
            x.append( "%d %s directly" % (protomonster.directKillCount, "killed" if not protomonster.nonalive else "destroyed" )  )
        if x:
            x = " (" + ", of which ".join( x ) + ")"
        else:
            x = ""
        print >>f, "\t", protomonster.name.amount( protomonster.spawnCount ), x

    f.close()
