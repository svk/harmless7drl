import Image
import ImageDraw
import ImageFont
import string
import itertools

fontsize = 14
width = 8
height = 12

lines = [
    [ chr(i) for i in range(32,64) ],
    ['@', '[', '\\', ']', '^', '_', '`', '{', '|', '}', '~' ],
    [],
    string.ascii_uppercase,
    string.ascii_lowercase,
]
flattened = itertools.chain( *lines )
maxlinelen = max( map( lambda t : len(t), lines ))

dimensions = maxlinelen * width, len(lines) * height

font = ImageFont.truetype( "VeraMono.ttf", fontsize )

def getLetter( ch ):
    return font.getmask( ch, "L" )

for letter in flattened:
    img = getLetter( letter )
    print letter, img, img.width, img.height
