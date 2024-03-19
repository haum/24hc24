#! /usr/bin/env python
# -*- coding:utf8 -*-
#
# this.py
#
# Copyright © 2024 Mathieu Gaborit (matael) <mathieu@matael.org>
#
# Licensed under the "THE BEER-WARE LICENSE" (Revision 42):
# Mathieu (matael) Gaborit wrote this file. As long as you retain this notice
# you can do whatever you want with this stuff. If we meet some day, and you
# think this stuff is worth it, you can buy me a beer or coffee in return
#

import math
import re

class MapIO:

    b64_digits = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"

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


if __name__ == '__main__':
    ratios = [0, 1/3, 2/3, 1]
    with open('web_viewer/game1.log', 'r') as fh:
        map_section = []
        while True:
            line = fh.readline()
            if (m := re.match(r'^MAP (\d+) (\d+) (\d+)$', line)):
                Nx, Ny, Nz = m.groups()
                print(Nx, Ny, Nz)
                break
        while True:
            line = fh.readline()
            if line == 'ENDMAP\n':
                break
            map_section.append(line)

        mapdata = re.sub(r'[^A-Za-z0-9\+\/]', '', ''.join(map_section))
        all_blocks = re.findall(r'.{3}', mapdata)
        decoded = []
        count = 0
        arrival_found = False
        for block in all_blocks:
            count += 1
            if block == 'AAA':
                continue
            nb = MapIO.b64_atoi(block)
            px = ratios[(nb & (3 << 0)) >> 0]
            mx = ratios[(nb & (3 << 2)) >> 2]
            py = ratios[(nb & (3 << 4)) >> 4]
            my = ratios[(nb & (3 << 6)) >> 6]
            pz = ratios[(nb & (3 << 8)) >> 8]
            mz = ratios[(nb & (3 << 10)) >> 10]
            bt = (nb & (7 << 12)) >> 12
            decoded.append((bt, px, py, pz, mx, my, mz))
            if bt == 0:
                arrival_found = True

        assert count == int(Nx) * int(Ny) * int(Nz)
        assert arrival_found
