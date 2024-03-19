#!/usr/bin/env python3
import random
from this import MapIO

def createBlock():
    bt = random.randint(0,7)
    px = random.randint(1,3)
    py = random.randint(1,3)
    pz = random.randint(1,3)
    mx = random.randint(1,3)
    my = random.randint(1,3)
    mz = random.randint(1,3)
    return MapIO.block_to_b64(bt,px,py,pz,mx,my,mz)

minx = 5
miny = 5
minz = 1

maxx = 5 
maxy = 5
maxz = 1

boxmaxx = random.randint(minx, maxx)
boxmaxy = random.randint(miny, maxy)
boxmaxz = random.randint(minz, maxz)

startx = random.randint(0, boxmaxx-1)
starty = random.randint(0, boxmaxy-1)
startz = random.randint(0, boxmaxz-1)

maxRandom4Block = 15

#print("On construit une map de dimension {},{},{} !".format(boxmaxx,boxmaxy,boxmaxz))

print("MAP {} {} {}".format(boxmaxx,boxmaxy,boxmaxz))
for z in range(boxmaxz):
    if z != 0:
        print("")
    for y in range(boxmaxy):
        for x in range(boxmaxx):
            randomBlock = random.randint(0,maxRandom4Block)
            if randomBlock == 2:
                block = createBlock()
            else:
                block = "AAA"
            if (x+1) == boxmaxx:
                print("{}".format(block))
            else:
                print("{} ".format(block), end='')

print("ENDMAP")
print("START {} {} {}".format(startx,starty,startz))


