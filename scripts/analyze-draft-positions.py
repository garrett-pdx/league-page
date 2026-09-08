#!/usr/bin/env python3
"""
One-off analysis: how does the Mudd League draft, positionally?

Answers two questions over the 2023-2025 drafts (real, single, primary drafts each --
no carryover-draft ambiguity in these seasons, unlike 2022):

  1. Round-by-round position mix -- does the league favor RBs over WRs (or vice versa)
     early, and does that hold across all three drafts?
  2. Does any manager tend to draft more than one QB or TE in a single draft?

Keeper picks are excluded throughout: a kept player occupies a draft slot but was never
a live draft-day decision this year, so counting it would misattribute a prior season's
choice to this one. Same reasoning and filter as derive-narratives.py's derive_draft_value().

Not wired into derive-narratives.py or any site route -- standalone analysis output only.

Run:  python3 scripts/analyze-draft-positions.py
Reads only committed files. No network, no Sleeper calls.
"""

import json
import os
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "static", "data")

OUT_DIR = "/private/tmp/claude-501/-Users-garrettcheadle-league-page/58d69364-170d-4b37-ba46-f44776042269/scratchpad"


def load(name):
    with open(os.path.join(DATA, name)) as f:
        return json.load(f)


HISTORY = load("league-history.json")
PLAYERS = load("players.json")
MANAGERS = HISTORY["managers"]

POS_ALIAS = {"FB": "RB"}
SEASONS = ["2023", "2024", "2025"]


def handle(user_id):
    return MANAGERS.get(user_id, {}).get("handle", user_id)


def ppos(pid):
    raw = PLAYERS.get(str(pid), {}).get("p", "?")
    return POS_ALIAS.get(raw, raw)


def draft_picks(season):
    drafts = [d for d in HISTORY["drafts"].get(season, []) if d.get("primary")]
    if not drafts:
        return []
    return [p for p in drafts[0]["picks"] if not p.get("is_keeper") and p.get("player_id")]


def main():
    round_pos_combined = defaultdict(lambda: defaultdict(int))
    round_pos_by_season = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    season_pick_counts = {}

    for season in SEASONS:
        picks = draft_picks(season)
        season_pick_counts[season] = len(picks)
        for p in picks:
            pos = ppos(p["player_id"])
            round_pos_combined[p["round"]][pos] += 1
            round_pos_by_season[season][p["round"]][pos] += 1

    manager_season_qbte = []
    for uid, minfo in MANAGERS.items():
        for season in SEASONS:
            # Football_Team never held a roster (present in 2022 user list only, 0-0 career)
            # and JJJet (Jordan Leonard) played 2022 only -- skip seasons a manager wasn't
            # actually in the league, rather than reporting a misleading 0/0.
            if season not in minfo.get("seasons", []):
                continue
            counts = {"QB": 0, "TE": 0}
            for p in draft_picks(season):
                if p["picked_by"] != uid:
                    continue
                pos = ppos(p["player_id"])
                if pos in counts:
                    counts[pos] += 1
            manager_season_qbte.append({
                "manager": handle(uid),
                "season": season,
                "QB": counts["QB"],
                "TE": counts["TE"],
                "flag": counts["QB"] >= 2 or counts["TE"] >= 2,
            })

    result = {
        "seasons": SEASONS,
        "season_pick_counts": season_pick_counts,
        "rounds_combined": {str(r): dict(v) for r, v in sorted(round_pos_combined.items())},
        "rounds_by_season": {
            season: {str(r): dict(v) for r, v in sorted(rounds.items())}
            for season, rounds in round_pos_by_season.items()
        },
        "manager_season_qbte": manager_season_qbte,
    }

    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, "draft-position-analysis.json")
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)

    print(json.dumps(result, indent=2))
    print(f"\nWrote {out_path}", flush=True)


if __name__ == "__main__":
    main()
