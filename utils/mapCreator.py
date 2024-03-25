#!/usr/bin/env python3
import random
import argparse
from map import Map

def createBlock():
    bt = random.randint(0,7)
    px = random.randint(1,3)
    py = random.randint(1,3)
    pz = random.randint(1,3)
    mx = random.randint(1,3)
    my = random.randint(1,3)
    mz = random.randint(1,3)
    return Map.block_to_b64(bt,px,py,pz,mx,my,mz)

parser = argparse.ArgumentParser()
parser.add_argument('--minx', '-x', type=int, default=1)
parser.add_argument('--miny', '-y', type=int, default=1)
parser.add_argument('--minz', '-z', type=int, default=1)
parser.add_argument('--maxx', '-X', type=int, default=25)
parser.add_argument('--maxy', '-Y', type=int, default=25)
parser.add_argument('--maxz', '-Z', type=int, default=25)
parser.add_argument('--randomness', '-r', type=int, default=20)
args = parser.parse_args()

boxmaxx = random.randint(args.minx, args.maxx)
boxmaxy = random.randint(args.miny, args.maxy)
boxmaxz = random.randint(args.minz, args.maxz)

startx = random.randint(0, boxmaxx-1)
starty = random.randint(0, boxmaxy-1)
startz = random.randint(0, boxmaxz-1)

#print("On construit une map de dimension {},{},{} !".format(boxmaxx,boxmaxy,boxmaxz))

print("MAP {} {} {}".format(boxmaxx,boxmaxy,boxmaxz))
for z in range(boxmaxz):
    if z != 0:
        print("")
    for y in range(boxmaxy):
        for x in range(boxmaxx):
            randomBlock = random.randint(0, args.randomness)
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


