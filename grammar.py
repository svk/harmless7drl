def makeList( l ):
    if not l:
        return "nothing"
    if len( l ) == 1:
        return l[0]
    return ", ".join( l[:-1]) + " and " + l[-1]

def capitalizeFirst( s ):
    return s[0].upper() + s[1:]
