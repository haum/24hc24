#!/usr/bin/env python3

import argparse
import re
import sys

from map import Map

class MapBuilder:
    def __init__(self, x, y, z, sx, sy, sz):
        self.Nx = x
        self.Ny = y
        self.Nz = z
        self.Sx = sx
        self.Sy = sy
        self.Sz = sz
        self.data = "AAA" * (x*y*z)

    def add_block(self, bt, x, y, z, px=3, py=3, pz=3, mx=None, my=None, mz=None):
        if mx is None: mx = px
        if my is None: my = py
        if mz is None: mz = pz
        if bt < 0 or bt >= 8: raise ValueError("Invalid bt value")
        if x < 0 or x >= self.Nx: raise ValueError("Invalid x value")
        if y < 0 or y >= self.Ny: raise ValueError("Invalid y value")
        if z < 0 or z >= self.Nz: raise ValueError("Invalid z value")
        if px < 0 or px >= 4: raise ValueError("Invalid px value")
        if py < 0 or py >= 4: raise ValueError("Invalid py value")
        if pz < 0 or pz >= 4: raise ValueError("Invalid pz value")
        if mx < 0 or mx >= 4: raise ValueError("Invalid mx value")
        if my < 0 or my >= 4: raise ValueError("Invalid my value")
        if mz < 0 or mz >= 4: raise ValueError("Invalid mz value")
        b = Map.block_to_b64(bt, px, py, pz, mx, my, mz)
        i = 3 * (x + y * self.Nx + z * self.Nx * self.Ny)
        self.data = self.data[:i] + b + self.data[i+3:]

    @property
    def str(self):
        mapdata = ''
        for i, a in enumerate(self.data):
            mapdata += a
            if ((i+1) % (3*self.Nx*self.Ny)) == 0: mapdata += '\n\n'
            elif ((i+1) % (3*self.Nx)) == 0: mapdata += '\n'
            elif ((i+1) % 3) == 0: mapdata += ' '
        mapdata = mapdata[:-2]
        return f'MAP {self.Nx} {self.Ny} {self.Nz}\n{mapdata}\nENDMAP\nSTART {self.Sx} {self.Sy} {self.Sz}\n'

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dimensions', '-d', nargs=3, type=int, metavar=('x', 'y', 'z'), default=(6, 3, 3))
    parser.add_argument('--initial-position', '-i', nargs=3, type=int, metavar=('x', 'y', 'z'), default=(0, 0, 0))
    parser.add_argument('--block', '-b', action='append', nargs=4, type=int, metavar=('bt','x', 'y', 'z'), dest='blocks')
    parser.add_argument('--block-symetric', '-s', action='append', nargs=7, type=int, metavar=('bt', 'x', 'y', 'z', 'px', 'py', 'pz'), dest='blocks')
    parser.add_argument('--block-asymetric', '-a', action='append', nargs=10, type=int, metavar=('bt', 'x', 'y', 'z', 'px', 'py', 'pz', 'mx', 'my', 'mz'), dest='blocks')
    args = parser.parse_args()

    mb = MapBuilder(*args.dimensions, *args.initial_position)
    print('New map of dimensions', args.dimensions, 'starting at', args.initial_position, file=sys.stderr)
    if args.blocks:
        for v in args.blocks:
            print('Add block', v, file=sys.stderr)
            mb.add_block(*v)

    print(mb.str, end='')
