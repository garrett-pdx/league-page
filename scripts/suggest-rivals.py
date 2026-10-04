#!/usr/bin/env python3
"""
Suggest a rival for every current manager, from the league's head-to-head history.

    python3 scripts/suggest-rivals.py           # print the pairings and why
    python3 scripts/suggest-rivals.py --write   # also set rival.userId in league.json

Every pair of current managers is scored on how often they have played (frequency), how close
those games were (closeness), and what rode on them (stakes: a playoff game counts three times a
regular-season one, a title game ten times; consolation games count as regular). The pairings are
then a maximum-weight perfect matching: everyone gets exactly one rival and nobody shares one,
which picking each manager's single best opponent cannot promise. With an odd number of
managers, one is left without a rival.

A suggestion, not a verdict: rivalries also come from history the data does not hold. --write
only fills rivals that are not already set. Reads static/data/games.json; run the pipeline first.
"""
import json
import os
import sys
from collections import defaultdict
from functools import lru_cache

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from league_config import CONFIG, CONFIG_PATH, DATA_DIR  # noqa: E402

STAKES = {"regular": 1.0, "consolation": 1.0, "exhibition": 0.5, "placement": 2.0, "playoff": 3.0}
TITLE = 10.0


def load_games():
    with open(os.path.join(DATA_DIR, "games.json")) as f:
        raw = json.load(f)
    col = dict(zip(raw["columns"], raw["data"]))
    games = []
    for i in range(raw["count"]):
        games.append({
            "season": col["season"][i], "week": col["week"][i],
            "a": raw["managers"][col["manager"][i]], "b": raw["managers"][col["opponent"][i]],
            "pf": col["pf"][i], "pa": col["pa"][i], "kind": raw["kinds"][col["kind"][i]],
        })
    return raw, games


def main():
    raw, games = load_games()
    with open(os.path.join(DATA_DIR, "league-history.json")) as f:
        history = json.load(f)
    if not games:
        print("no games yet; nothing to suggest")
        return 0
    current = max(g["season"] for g in games)
    people = sorted({g["a"] for g in games if g["season"] == current
                     and not history["managers"].get(g["a"], {}).get("orphan")})
    handle = lambda u: history["managers"].get(u, {}).get("handle", u)  # noqa: E731

    # The title game of each season: the last playoff week's game involving the champion.
    title_games = set()
    for season, table in history.get("final_standings", {}).items():
        champ = next((r["user_id"] for r in table if r["place"] == 1), None)
        weeks = [g["week"] for g in games if g["season"] == int(season) and g["kind"] == "playoff"]
        if champ and weeks:
            for g in games:
                if g["season"] == int(season) and g["kind"] == "playoff" and g["week"] == max(weeks) and g["a"] == champ:
                    title_games.add((int(season), g["week"], frozenset((g["a"], g["b"]))))

    pair = defaultdict(lambda: {"n": 0, "margin": 0.0, "stakes": 0.0, "wins": defaultdict(int)})
    for g in games:
        if g["a"] not in people or g["b"] not in people or g["a"] > g["b"]:
            continue  # each game once, current managers only
        p = pair[(g["a"], g["b"])]
        p["n"] += 1
        p["margin"] += abs(g["pf"] - g["pa"])
        key = (g["season"], g["week"], frozenset((g["a"], g["b"])))
        p["stakes"] += TITLE if key in title_games else STAKES.get(g["kind"], 1.0)
        p["wins"][g["a"] if g["pf"] > g["pa"] else g["b"] if g["pa"] > g["pf"] else "tie"] += 1

    def score(a, b):
        p = pair.get((min(a, b), max(a, b)))
        if not p or not p["n"]:
            return 0.0
        avg_margin = p["margin"] / p["n"]
        closeness = 1.0 / (1.0 + avg_margin / 15.0)  # a 15-point average margin halves it
        return p["stakes"] * (0.5 + closeness)

    n = len(people)
    if n > 22:
        print(f"{n} managers is more than this exact matcher handles quickly", file=sys.stderr)
        return 1

    @lru_cache(maxsize=None)
    def best(mask):
        """Best total over the managers not in mask; returns (total, pairs)."""
        free = [i for i in range(n) if not mask & (1 << i)]
        if len(free) < 2:
            return 0.0, ()
        i = free[0]
        options = []
        if len(free) % 2 == 1:  # odd: i may be the one left out
            t, ps = best(mask | (1 << i))
            options.append((t, ps))
        for j in free[1:]:
            t, ps = best(mask | (1 << i) | (1 << j))
            options.append((t + score(people[i], people[j]), ps + ((i, j),)))
        return max(options, key=lambda x: x[0])

    total, pairs = best(0)
    rivals = {}
    print(f"Suggested rivals for {n} current managers (stakes, meetings, record, average margin):")
    for i, j in pairs:
        a, b = people[i], people[j]
        p = pair.get((min(a, b), max(a, b)))
        rivals[a], rivals[b] = b, a
        rec = f"{p['wins'][a]}-{p['wins'][b]}" + (f"-{p['wins']['tie']}" if p["wins"]["tie"] else "") if p else "0-0"
        avg = p["margin"] / p["n"] if p and p["n"] else 0
        print(f"  {handle(a)} v {handle(b)}: score {score(a, b):.1f}, {p['n'] if p else 0} meetings, "
              f"{handle(a)} {rec}, avg margin {avg:.1f}")
    left = [u for u in people if u not in rivals]
    for u in left:
        print(f"  {handle(u)}: no rival (odd number of managers); league.json can name one, e.g. \"The Field\"")

    if "--write" in sys.argv:
        changed = 0
        for m in CONFIG.get("managers") or []:
            if m["userId"] in rivals and not (m.get("rival") or {}).get("userId") and not (m.get("rival") or {}).get("name"):
                m["rival"] = {"userId": rivals[m["userId"]]}
                changed += 1
        with open(CONFIG_PATH, "w") as f:
            f.write(json.dumps(CONFIG, indent=2, ensure_ascii=False) + "\n")
        print(f"set {changed} rival(s) in league.json (existing rivals left alone)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
