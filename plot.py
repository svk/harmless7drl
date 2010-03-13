from widgets import WallOfTextWidget

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
    game.main.query( WallOfTextWidget, width = 60, text = """\
It had seemed like such an easy job.\
\n
Grand Witch Adrachia had appointed you personal assistant to\
 Professor Nislakh, the Special Advisor on Magical Warfare. Now,\
 it was widely known that the title of "personal assistant" was a\
 euphemism. Your real job was to make sure he didn't run\
 away and did not work any unauthorized magic. Nislakh was a\
 magically animated automaton, a techno-magical wonder left over\
 from the war. Although his immense intelligence made him\
 an asset that the University could not afford to lose, as a\
 sentient weapon he had been programmed to be vicious to the core,\
 and if left to his own devices he would surely hatch some\
 insidious plot of mass destruction.""")
    game.main.query( WallOfTextWidget, width = 60, text = """\
Intellectually you were well aware that he was capable of this.\
 He'd been responsible for schemes that had cost thousands of\
 lives during the war. But since Professor Nislakh was a\
 cute little clockwork being of no more than sixteen inches,\
 walked with a ridiculous wobble, and communicated\
 verbally only in beeps and boops, it was, frankly, hard\
 to take him seriously as a threat to humankind. Besides, the University\
 had managed to reprogram him to be unable to directly harm a\
 human being in any way, and moreover, to fall asleep for forty-eight\
 hours at the sound of the word NIPLOP. With these safeguards,\
 surely being his minder should be the easiest job in the world.""")
    game.main.query( WallOfTextWidget, width = 60, text = """\
Or so you'd thought. Which is why you'd brought a novel with you,\
 to have something to do in between fetching books for the\
 Professor for his research. During a particularly exciting paragraph\
 of chapter thirty-six, you'd been rudely interrupted by a loud\
 magical-sounding noise and the disappearance of Professor Nislakh\
 and half the library into a vast magical portal.""")
    game.main.query( WallOfTextWidget, width = 60, text = """\
Now, you consider yourself a lover, not a fighter. But you're a\
 smart, resourceful girl, and you'll have the resources of the Applied Runic Magic\
 section of the library at your disposal if you can only manage to\
 recover them. And all you're up against is a little dungeon and a\
 miniscule robot that can't harm you.\
\n
Hoping that Adrachia will forgive your carelessness if you compensate\
 for it with a little reckless heroism, you jump in after the professor\
 to retrieve him.""")


def displayOutro( game, booksRetrieved ):
    game.main.query( WallOfTextWidget, width = 60, text = """\
Returning to the University with the Professor slung over your\
 shoulder, you are greeted as a hero by masses of students. As you\
 walk past them to face the Grand Witch, University magicians\
 seal the portal behind you.""")
    game.main.query( WallOfTextWidget, width = 60, text = """\
Adrachia chastises you for your recklessness but commends you for\
 your bravery and skill. [[ She also commends you on bringing back\
 N of the library's valuable magical books. // She does bemoan the\
 fact that so many of the library's books were lost.]]\
\n
She promises to reward you with a promotion as soon as she can\
 find a task more suited to your obvious magical talent and less\
 requiring of the exercise of prudence. For the moment, your work\
 as assistant to Nislakh is suspended, as he is confined to a\
 magical holding cell.\
\n
Having saved the world and lived to tell the tale, you breathe\
 a sigh of relief and prepare to do just that.""")
    game.main.query( WallOfTextWidget, width = 60, text = """\
Congratulations on your victory! A log file has been written to\
 the game directory. (not really yet)""")
