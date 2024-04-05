#!/usr/bin/env python
# -*- coding:utf8 -*-

import itertools
from collections import namedtuple

from map import Map

def bruteforce_solve(m, stop_at_first=False, progress=False):
    if not m.valid: return [], 0

    StateInfo = namedtuple('StateInfo', 'moves prevstate Ax Ay Az'.split())
    initial_state = Map.State(m.Sx, m.Sy, m.Sz, 0, 0, 0, 0)
    infos = { initial_state: StateInfo(0, initial_state, 0, 0, 0) }
    toexplore = set()
    toexplore.add(initial_state)
    finalstateinfo = None

    try:
        count = 0
        while toexplore:
            state = toexplore.pop()
            if finalstateinfo and infos[state].moves > finalstateinfo.moves: continue
            count += 1
            if progress:
                if count & 0xfff == 0:
                    print(f".", file=sys.stderr, end="\n" if count & 0xffff == 0 else "")
                    sys.stderr.flush()
            for Ax, Ay, Az in itertools.product((-1, 0, 1), (-1, 0, 1), (-1, 0, 1)):
                result = m.analyze_path_step(state, Ax, Ay, Az)
                if isinstance(result, Map.State):
                    nmoves = infos[state].moves + 1
                    if result in infos:
                        if nmoves < infos[result].moves:
                            infos[result] = StateInfo(nmoves, state, Ax, Ay, Az)

                    else:
                        toexplore.add(result)
                        infos[result] = StateInfo(nmoves, state, Ax, Ay, Az)
                else:
                    if result.ok:
                        nmoves = infos[state].moves + result.moves
                        accepted = not finalstateinfo or nmoves < finalstateinfo.moves
                        if progress:
                            if accepted:
                                print(f"Found: {nmoves} moves", file=sys.stderr)
                            else:
                                print(f"Rejected found: {nmoves} moves", file=sys.stderr)
                        if accepted:
                            finalstateinfo = StateInfo(nmoves, state, Ax, Ay, Az)
                        if stop_at_first:
                            toexplore.clear()
    except KeyboardInterrupt:
        pass

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
    parser.add_argument('--deep', '-d', action='store_true', help="Deeper search")
    args = parser.parse_args()

    with open(args.map_file, 'r') as f:
        the_map = Map(f.read())

    path, moves = bruteforce_solve(the_map, not args.deep, True)

    if not path:
        print("No path found")
    for a in path:
        print('ACC', ' '.join(map(str, a)))
    print("Moves:", moves, file=sys.stderr)
