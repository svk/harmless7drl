import cerealizer as c
import gzip
from grammar import capitalizeFirst

# Saving a game: basically saving/restoring the "context"
# object, and all it points to
# Things that must be regenerated:
#   - the level generator thread (duh)

# the one thing serialization does mean is that we can't
# safely save lambdas. save objects instead, as these
# can be restricted in activities (e.g. a Trap never
# does anything except trigger a trap)

# this means that e.g. one class for each AI is absolutely
# required.

Signature = "Harmless7DRL"
Version = 0.1

class InvalidSaveException: pass


class GameContext:
    def log(self, s):
        try:
            self.game.log( capitalizeFirst(s) )
        except AttributeError:
            pass
    def neuter(self):
        rv = {}
#        rv[ 'levelGenerator' ] = self.levelGenerator
#        del self.levelGenerator
        try:
            rv[ 'gameWidget' ] = self.game
            del self.game
        except AttributeError:
            pass
        return rv
    def unneuter(self, data):
#        self.levelGenerator = data['levelGenerator']
        try:
            self.game = data['gameWidget']
        except KeyError:
            pass
    def save(self, filename ):
        unsaved = self.neuter()
        try:
            f = gzip.GzipFile( filename, "wb" )
            c.dump( Signature, f )
            c.dump( Version, f )
            c.dump( self, f )
            f.close()
        finally:
            self.unneuter( unsaved )
    def load(self, filename ):
        unsaved = self.neuter() # used to unneuter the restored object
        try:
            f = gzip.GzipFile( filename, "rb" )
            if c.load( f ) != Signature: raise InvalidSaveException()
            if c.load( f ) != Version: raise InvalidSaveException()
            rv = c.load( f )
            rv.unneuter( unsaved )
            return rv
        except:
            self.unneuter( unsaved )
            raise

def registerClasses():
    c.register( GameContext )
    import level as L
    c.register( L.Mobile )
    c.register( L.Map )
    c.register( L.Tile )
    c.register( L.Item )
    c.register( L.Rarity )
    import grammar as G
    c.register( G.Noun )
    c.register( G.ProperNoun )
    c.register( G.Verb )
    import timing as T
    c.register( T.Simulator )
    c.register( T.EventWrapper )
    import traps as R # curses, foiled again
    c.register( R.Trap )
    c.register( R.SpikePit )
    c.register( R.ExplodingMine )
    c.register( R.TrapDoor )
    import ai as A
    c.register( A.RandomWalker )
    c.register( A.TurnerBot )
    import magic as M
    c.register( M.Rune )
    c.register( M.Spell )
    c.register( M.Tome )
    c.register( M.TrapTalisman )
    c.register( M.HealthTalisman )
    c.register( M.Staff )
    c.register( M.Dig )
    c.register( M.HealSelf )
    c.register( M.LevitateSelf )

def saveObject( o, filename ):
    # overwrites without warning!
    f = gzip.GzipFile( filename, "wb" )
    c.dump( o, f )
    c.dump( o, f )
    f.close()

def loadObject( filename ):
    f = gzip.GzipFile( filename, "rb" )
    o = c.load( f )
    o2 = c.load( f )
    f.close()
    return o, o2

def initializeSerialization():
    registerClasses()
    c.freeze_configuration()
