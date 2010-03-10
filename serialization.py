import cerealizer as c
import gzip

# Saving a game: basically saving/restoring the "context"
# object, and all it points to
# Things that must be regenerated:
#   - the level generator thread (duh)

Signature = "Harmless7DRL"
Version = 0.1

class InvalidSaveException: pass


class GameContext:
    def log(self, s):
        try:
            self.game.log( s )
        except AttributeError:
            pass
    def neuter(self):
        rv = {}
        rv[ 'levelGenerator' ] = self.levelGenerator
        del self.levelGenerator
        try:
            rv[ 'gameWidget' ] = self.game
            del self.game
        except AttributeError:
            pass
        return rv
    def unneuter(self, data):
        self.levelGenerator = data['levelGenerator']
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
    import grammar as G
    c.register( G.Noun )
    c.register( G.ProperNoun )
    import timing as T
    c.register( T.Simulator )
    c.register( T.EventWrapper )
    import ai as A
    c.register( A.RandomWalker )
    c.register( A.HugBot )

registerClasses()
c.freeze_configuration()


def saveObject( o, filename ):
    # overwrites without warning!
    f = gzip.GzipFile( filename, "wb" )
    c.dump( o, f )
    c.dump( o, f )
    f.close()

def loadObject( o, filename ):
    f = gzip.GzipFile( filename, "rb" )
    o = c.load( f )
    o2 = c.load( f )
    f.close()
    return o, o2
