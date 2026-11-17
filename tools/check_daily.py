#!/usr/bin/env python3
"""Proves the daily page plays the puzzle book the way the game does.
usage: python3 tools/check_daily.py <path to the swanroad-sim checkout>

1. The book written into daily/index.html is the app's book (app/Swanroad/Resources/puzzles.json), puzzle for puzzle.
2. The simulator (sim.py) plays every legal move from every position a solution passes through. The results go to a
   fixture, and tools/check_daily.mjs plays the same moves through daily/puzzle.js and compares what is legal and the
   board, hands, scores and turn after each move. It also checks which puzzle the page picks for a day, at local
   midnight in several time zones, and who is sent to the app.

Run it after tools/puzzle_pages.py whenever the app's book or daily/puzzle.js changes. Needs node."""
import json, pathlib, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
if len(sys.argv) != 2:
    sys.exit(__doc__)
SIM = pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0, str(SIM))
import sim  # noqa: E402

FIRST_MIXED_DAY = 20746  # PuzzleStore.firstMixedDay in the app


def token(a):
    return {"P": lambda: f"P{a[1]}", "S": lambda: f"S{a[1]}-{a[2]}", "L": lambda: f"L{a[1]}", "X": lambda: "X"}[a[0]]()


def parse(tok):
    if tok[0] == "S":
        a, b = tok[1:].split("-")
        return ("S", int(a), int(b))
    return (tok[0], int(tok[1:]))


def plain(state):
    cells, supply, score, to_move, turn = state[:5]
    return {"cells": "".join(str(c) for c in cells), "supply": list(supply), "score": list(score), "toMove": to_move, "turn": turn}


def positions(p):
    """Every position the solution passes through with the solver to move, and how many moves are left there."""
    start = (tuple(int(c) for c in p["cells"]), tuple(p["supply"]), tuple(p["score"]), p["toMove"], p["turn"], (None, 0, 0))
    out = []

    def walk(state, node, left):
        out.append((state, node, left))
        for tok, child in node.items():
            if child is None:
                continue
            after = sim.apply(state, parse(tok))[0]
            walk(sim.apply(after, parse(child["reply"]))[0], child["then"], left - 1)

    walk(start, p["tree"], p["n"])
    return out


def daily_index(day, count):
    """PuzzleStore.daily(on:), written out again from the Swift."""
    if day < FIRST_MIXED_DAY:
        return day % count
    step = 29
    while __import__("math").gcd(step, count) != 1:
        step += 1
    return ((day - FIRST_MIXED_DAY) * step) % count


book = json.load(open(SIM / "app" / "Swanroad" / "Resources" / "puzzles.json"))
cases, moves = [], 0
for p in book["puzzles"]:
    for state, node, left in positions(p):
        results = {}
        for act in sim.legal_actions(state):
            results[token(act)] = plain(sim.apply(state, act)[0])
        moves += len(results)
        cases.append({"id": p["id"], "left": left, "winning": sorted(node), "state": plain(state), "results": results})

count = len(book["puzzles"])
fixture = {
    "book": book,
    "cases": cases,
    "days": {str(d): daily_index(d, count) for d in list(range(FIRST_MIXED_DAY - 100, FIRST_MIXED_DAY + 400))},
}
print(f"simulator: {len(cases)} positions and {moves} moves from {count} puzzles")
with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
    json.dump(fixture, f)
try:
    sys.exit(subprocess.run(["node", str(ROOT / "tools" / "check_daily.mjs"), f.name]).returncode)
finally:
    pathlib.Path(f.name).unlink(missing_ok=True)
