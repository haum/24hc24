#!/usr/bin/env python
# -*- coding:utf8 -*-

from collections import namedtuple
from enum import Enum
import math
import re

class Map:

    b64_digits = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    mapdesc_pattern = re.compile(r"^\n*MAP (\d+) (\d+) (\d+)\n+([a-zA-Z0-9+/\n\s]+)\n+ENDMAP\n+START (\d+) (\d+) (\d+)\n*$", re.MULTILINE)
    pathdesc_pattern = re.compile(r"^ACC (-?\d+) (-?\d+) (-?\d+)$")
    BlockType = Enum('BlockType', ['GOAL', 'ASTEROID', 'NEBULA', 'MAGCLOUD', 'CP1', 'CP2', 'CP3', 'CP4'])
    BlockInfo = namedtuple('BlockInfo', 'bt px py pz mx my mz empty'.split())
    PathAnalysis = namedtuple('PathAnalysis', 'ok moves msg'.split())

    @classmethod
    def b64_itoa(cls, n):
        string = ''
        nb = math.floor(n)
        while nb > 0:
            string = cls.b64_digits[nb % 64] + string
            nb = math.floor(nb / 64)
        return string

    @classmethod
    def b64_atoi(cls, string):
        nb = 0
        for c in string:
            nb = nb * 64 + cls.b64_digits.index(c)
        return nb

    @classmethod
    def block_to_b64(cls, bt, px, py, pz, mx, my, mz):
        nb = ((px & 3) << 0) +\
            ((mx & 3) << 2) +\
            ((py & 3) << 4) +\
            ((my & 3) << 6) +\
            ((pz & 3) << 8) +\
            ((mz & 3) << 10) +\
            ((bt & 7) << 12)
        return ('AAA' + cls.b64_itoa(nb))[-3:]

    @classmethod
    def decode_block(cls, block):
        nb = cls.b64_atoi(block)
        px = (nb & (3 << 0)) >> 0
        mx = (nb & (3 << 2)) >> 2
        py = (nb & (3 << 4)) >> 4
        my = (nb & (3 << 6)) >> 6
        pz = (nb & (3 << 8)) >> 8
        mz = (nb & (3 << 10)) >> 10
        bt = (nb & (7 << 12)) >> 12
        bte = cls.BlockType(bt+1)
        return cls.BlockInfo(bte, px, py, pz, mx, my, mz, block=='AAA')

    def __init__(self, mapdesc):
        m = self.mapdesc_pattern.match(mapdesc)
        self.maxcp = None
        if m:
            Nx, Ny, Nz, data, Sx, Sy, Sz = m.groups()
            self.Nx, self.Ny, self.Nz, self.Sx, self.Sy, self.Sz = map(int, (Nx, Ny, Nz, Sx, Sy, Sz))
            self.blocks = re.findall('...', ''.join(data.split()))
        else:
            self.Nx, self.Ny, self.Nz, self.Sx, self.Sy, self.Sz = [0]*6
            self.blocks = []

    def __getitem__(self, t):
        x, y, z = t
        return self.decode_block(self.blocks[x + y * self.Nx + z * self.Nx * self.Ny])

    def __iter__(self):
        for b in self.blocks:
            yield self.decode_block(b)

    @property
    def start(self):
        return self[m.Sx, m.Sy, m.Sz]

    @property
    def valid(self):
        return not self.find_error()

    def find_error(m, max_width = 25): # max_width included
        """Analyse the map structure and return an error message if an error is found, None otherwise.
        The errors are checked in the following order:
        - Invalid global structure
        - Invalid dimensions
        - Invalid start point
        - Wrong number of blocks
        - Start in forbidden block
        - Invalid block
        - No arrival found
        - Invalid checkpoints
        """

        if not m.blocks:
            return "Invalid global structure"

        if m.Nx < 0 or m.Nx > max_width or \
           m.Ny < 0 or m.Ny > max_width or \
           m.Nz < 0 or m.Nz > max_width:
               return "Invalid dimensions"

        if m.Sx < 0 or m.Sx >= m.Nx or \
           m.Sy < 0 or m.Sy >= m.Ny or \
           m.Sz < 0 or m.Sz >= m.Nz:
               return "Invalid start point"

        if len(m.blocks) != m.Nx*m.Ny*m.Nz:
            return 'Wrong number of blocks'

        bs = m.start
        if not bs.empty and \
           bs.bt in (Map.BlockType.GOAL, Map.BlockType.ASTEROID) and \
           bs.px * bs.mx * bs.py * bs.my * bs.pz * bs.mz != 0:
            return "Start in forbidden block"

        arrival = False
        cp1 = False
        cp2 = False
        cp3 = False
        cp4 = False
        for b in m:
            if b.empty: continue

            if b.bt == Map.BlockType.GOAL: arrival = True
            elif b.bt == Map.BlockType.CP1: cp1 = True
            elif b.bt == Map.BlockType.CP2: cp2 = True
            elif b.bt == Map.BlockType.CP3: cp3 = True
            elif b.bt == Map.BlockType.CP4: cp4 = True

            if (b.px == b.mx and b.mx == 0) or \
               (b.py == b.my and b.my == 0) or \
               (b.pz == b.mz and b.mz == 0):
                return 'Invalid block'

        if not arrival:
            return 'No arrival'

        if (cp2 and not cp1) or \
           (cp3 and not cp2) or \
           (cp4 and not cp3):
            return 'Invalid checkpoints'

        if cp4: m.maxcp = 4
        elif cp3: m.maxcp = 3
        elif cp2: m.maxcp = 2
        elif cp1: m.maxcp = 1
        else: m.maxcp = 0

        return None

    def check_path(self, pathdesc):
        return self.analyze_path(pathdesc).ok

    def analyze_path(self, pathdesc): # Not complete !!!
        moves = 0
        checkpoint = 0
        victory = False
        Vx, Vy, Vz = 0, 0, 0
        Px, Py, Pz = self.Sx, self.Sy, self.Sz
        for p in filter(None, pathdesc.splitlines()):
            if victory:
                return self.PathAnalysis(False, moves, "Moves after destination")

            m = self.pathdesc_pattern.match(p)
            if not m: return self.PathAnalysis(False, moves, "Invalid line syntax")

            Ax, Ay, Az = map(int, m.groups())
            if Ax not in (-1, 0, 1) or \
               Ay not in (-1, 0, 1) or \
               Az not in (-1, 0, 1):
                return self.PathAnalysis(False, moves, "Invalid acceleration")

            bs = self[Px, Py, Pz]
            if bs.bt == self.BlockType.MAGCLOUD:
                if Ax or Ay or Az:
                    return self.PathAnalysis(False, moves, "Invalid acceleration in magnetic cloud")
            if bs.bt == self.BlockType.NEBULA:
                nVx, nVy, nVz = Vx+Ax, Vy+Ay, Vz+Az
                if (abs(nVx) > 1 and abs(nVx) >= abs(Vx)) or \
                   (abs(nVy) > 1 and abs(nVy) >= abs(Vy)) or \
                   (abs(nVz) > 1 and abs(nVz) >= abs(Vz)):
                    return self.PathAnalysis(False, moves, "Invalid acceleration in nebula")

            Vx, Vy, Vz = Vx+Ax, Vy+Ay, Vz+Az
            Px, Py, Pz = Px+Vx, Py+Vy, Pz+Vz
            moves += 1

            if Px < 0 or Px >= self.Nx or \
               Py < 0 or Py >= self.Ny or \
               Pz < 0 or Pz >= self.Nz:
                   submoves = 0 # TODO
                   return self.PathAnalysis(False, moves + submoves - 1, "Out of the universe")

            intersections = [(self[Px, Py, Pz], 1)] # TODO Should find intersecting blocks
            for bc, submoves in intersections:
                if bc.bt == self.BlockType.ASTEROID:
                    if not victory:
                        return self.PathAnalysis(False, moves + submoves - 1, "Collision")
                elif bc.bt == self.BlockType.GOAL:
                    if not bc.empty:
                        if self.maxcp is None:
                            maxcp = 0
                            for b in m:
                                if b.bt == self.BlockType.CP1: maxcp = max(maxcp, 1)
                                elif b.bt == self.BlockType.CP2: maxcp = max(maxcp, 2)
                                elif b.bt == self.BlockType.CP3: maxcp = max(maxcp, 3)
                                elif b.bt == self.BlockType.CP4: maxcp = max(maxcp, 4)
                            self.maxcp = maxcp
                        if checkpoint == self.maxcp:
                            victory = True
                            moves = moves + submoves - 1
                elif bc.bt == self.BlockType.CP1:
                    if checkpoint == 0: checkpoint += 1
                elif bc.bt == self.BlockType.CP2:
                    if checkpoint == 1: checkpoint += 1
                elif bc.bt == self.BlockType.CP3:
                    if checkpoint == 2: checkpoint += 1
                elif bc.bt == self.BlockType.CP4:
                    if checkpoint == 3: checkpoint += 1

        if victory:
            return self.PathAnalysis(True, moves, "Victory")
        return self.PathAnalysis(False, moves, "Mission not completed")


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print(f"Usage : {sys.argv[0]} <map_file> [path_file]")
        exit()

    with open(sys.argv[1], 'r') as f:
        m = Map(f.read())
        print(m.valid, m.find_error())

    if len(sys.argv) > 2:
        with open(sys.argv[2], 'r') as f:
            p = f.read()
            print(m.check_path(p), m.analyze_path(p))
