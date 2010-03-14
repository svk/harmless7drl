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

class InvalidSaveException: pass


class GameContext:
    def __init__(self):
        from grammar import ProperNoun
        import random
        from monsters import MacGuffinMobileMale, MacGuffinMobileFemale
        from items import MacGuffinMale, MacGuffinFemale
        # some mad libs for the plot
        self.bossName = ProperNoun( "Askarmon", "male" ) if random.randint(0,1) else ProperNoun( "Adrachia", "female" )
        self.bossTitle = "High Wizard" if self.bossName.gender == "male" else "Grand Witch"
        self.macGuffinMobile = MacGuffinMobileMale if random.randint(0,1) else MacGuffinMobileFemale
        self.macGuffin = MacGuffinMale if self.macGuffinMobile.name.gender == "male" else MacGuffinFemale
        self.totalTime = 0
        self.debugmode = False
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
            from harmless7drl import Signature, Version
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
            from harmless7drl import Signature, Version
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
    c.register( R.ArrowTrap )
    c.register( R.TeleportationTrap )
    c.register( R.RockslideTrap )
    c.register( R.NonlethalPit )
    c.register( R.UncoveredHole )
    import ai as A
    c.register( A.RandomWalker )
    c.register( A.TurnerBot )
    c.register( A.MeleeSeeker )
    c.register( A.IncorporealSeeker )
    c.register( A.MeleeMagicHater )
    c.register( A.Rook )
    c.register( A.BoulderAi )
    c.register( A.DebufferAi )
    c.register( A.StaffStealer )
    c.register( A.DigAnimal )
    c.register( A.ExplodesOnDeathHook )
    c.register( A.PlayerTrailFollower )
    c.register( A.PursueWoundedAnimal )
    c.register( A.ChokepointSleeperAnimal )
    c.register( A.SpawnProtectorAnimal )
    c.register( A.SpawnAnimal )
    import magic as M
    c.register( M.Rune )
    c.register( M.Treasure )
    c.register( M.Spell )
    c.register( M.Tome )
    c.register( M.TrapTalisman )
    c.register( M.HealthTalisman )
    c.register( M.Staff )
    c.register( M.Dig )
    c.register( M.HealSelf )
    c.register( M.LevitateSelf )
    c.register( M.TeleportSelf )
    c.register( M.TeleportOther )
    c.register( M.Invisibility )
    c.register( M.MagicMap )
    c.register( M.FlyerKnockback )
    c.register( M.Visions )
    c.register( M.Pacify )
    c.register( M.CalmAirSpell )
    c.register( M.SummonBoulder )
    c.register( M.Rockform )
    c.register( M.DetectLivingMonsters )

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
