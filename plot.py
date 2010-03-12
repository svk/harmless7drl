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
