import Image
import ImageDraw
import ImageFont
import string
import itertools
import sys

fontfile = "ttf-bitstream-vera-1.10/VeraMono.ttf"
fontsize = 20
lines = [
    [ chr(i) for i in range(32,64) ],
    ['@', '[', '\\', ']', '^', '_', '`', '{', '|', '}', '~' ],
    [],
    string.ascii_uppercase,
    string.ascii_lowercase,
    [],
    [],
    []
]
flattened = itertools.chain( *lines )
maxlinelen = max( map( lambda t : len(t), lines ))

font = ImageFont.truetype( fontfile, fontsize )

def getLetter( ch ):
    return font.getmask( ch, "L" )

minwidth, minheight = 1000, 1000
width, height = 0, 0
for letter in flattened:
    img = getLetter( letter )
    w, h = img.size
    width = max( w, width )
    height = max( h, height )
    minwidth = min( w, minwidth )
    minheight = min( h, minheight )
print >> sys.stderr, "font:", fontfile, fontsize
print >> sys.stderr, "dimensions:", width, height
print >> sys.stderr, "maximal mismatch:", width - minwidth, height - minheight
dimensions = maxlinelen * width, len(lines) * height

output = Image.new( "RGB", dimensions )
draw = ImageDraw.Draw( output )
y = 0
for line in lines:
    x = 0
    for letter in line:
        draw.text( (x,y), letter, font = font, fill = (255,255,255) )
        x += width
    y += height
output.save( "/home/kaw/www/misc/font-output.png" )

print >> sys.stderr, "image produced"
