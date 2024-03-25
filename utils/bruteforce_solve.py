#!/usr/bin/env python
# -*- coding:utf8 -*-

import itertools
from collections import namedtuple

from map import Map

def bruteforce_solve(m, stop_at_first=False):
    if not m.valid: return []

    StateInfo = namedtuple('StateInfo', 'moves prevstate Ax Ay Az'.split())
    initial_state = Map.State(m.Sx, m.Sy, m.Sz, 0, 0, 0, 0)
    infos = { initial_state: StateInfo(0, initial_state, 0, 0, 0) }
    toexplore = set()
    toexplore.add(initial_state)
    finalstateinfo = None

    while toexplore:
        state = toexplore.pop()
        for Ax, Ay, Az in itertools.product((-1, 0, 1), (-1, 0, 1), (-1, 0, 1)):
            result = m.analyze_path_step(state, Ax, Ay, Az)
            if isinstance(result, Map.State):
                if result in infos:
                    nmoves = infos[state].moves + 1
                    if nmoves < infos[result].moves:
                        infos[result] = StateInfo(nmoves, state, Ax, Ay, Az)

                else:
                    toexplore.add(result)
                    infos[result] = StateInfo(infos[state].moves+1, state, Ax, Ay, Az)
            else:
                if result.ok:
                    if not finalstateinfo:
                        finalstateinfo = StateInfo(infos[state].moves+result.moves, state, Ax, Ay, Az)
                    else:
                        nmoves = infos[state].moves + result.moves
                        if nmoves < finalstateinfo.moves:
                            finalstateinfo = StateInfo(nmoves, state, Ax, Ay, Az)
                    if stop_at_first:
                        toexplore.clear()
    if finalstateinfo:
        path = []
        p = finalstateinfo
        while p.moves != 0:
            path = [(p.Ax, p.Ay, p.Az)] + path
            p = infos[p.prevstate]
        return path, finalstateinfo.moves
    return [], 0

if __name__ == '__main__':
    import argparse, sys
    parser = argparse.ArgumentParser()
    parser.add_argument('map_file')
    parser.add_argument('--stop_at_first', '-s', action='store_true')
    args = parser.parse_args()

    with open(args.map_file, 'r') as f:
        the_map = Map(f.read())

    path, moves = bruteforce_solve(the_map, args.stop_at_first)

    if not path:
        print("No path found")
    for a in path:
        print('ACC', ' '.join(map(str, a)))
    print("Moves:", moves, file=sys.stderr)
