import cerealizer as c
import gzip


def save( o, filename ):
    # overwrites without warning!
    f = gzip.GzipFile( filename, "wb" )
    c.dump( o, f )
    f.close()

def load( o, filename ):
    f = gzip.GzipFile( filename, "rb" )
    o = c.load( f )
    f.close()
    return o

if __name__ == '__main__':
    from levelgen import generateLevel, LevelGenerator, Room
    c.register( LevelGenerator )
    c.register( Room )
    lev = generateLevel( 100, 100 )
    save( lev, "test-serialization.gz" )
    lev = load( lev, "test-serialization.gz" )
    for line in lev.data:
        print "".join( line )
