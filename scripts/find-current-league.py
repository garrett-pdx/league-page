#!/usr/bin/env python3
"""
Has Sleeper rolled the league over to a new season? Find the newest league in the chain.

    python3 scripts/find-current-league.py            # report
    python3 scripts/find-current-league.py --write    # also update league.json

Sleeper gives a league a new ID every season when it is renewed, and the old ID keeps working,
frozen. The site reads the CURRENT season's ID from league.json and walks previous_league_id
backwards for history, so after a renewal nothing breaks: the site just quietly stays on last
season. This finds the newer league by looking through the configured league's managers' leagues
for later seasons, keeping one whose previous_league_id points back at the configured one, and
repeats until there is nothing newer. Stdlib only. Needs network.
"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from league_config import CONFIG, CONFIG_PATH, LEAGUE_ID  # noqa: E402

API = "https://api.sleeper.app/v1"


def get(path):
    with urllib.request.urlopen(f"{API}/{path}", timeout=30) as r:
        return json.loads(r.read())


def newer(league):
    """The league renewed from this one, or None."""
    season = int(league["season"])
    users = get(f"league/{league['league_id']}/users") or []
    for u in users[:12]:  # any manager who stayed finds it; a few is plenty
        for nxt in (season + 1, season + 2):
            for lg in get(f"user/{u['user_id']}/leagues/nfl/{nxt}") or []:
                if lg.get("previous_league_id") == league["league_id"]:
                    return lg
    return None


def main():
    league = get(f"league/{LEAGUE_ID}")
    chain = [league]
    while True:
        nxt = newer(chain[-1])
        if not nxt:
            break
        chain.append(get(f"league/{nxt['league_id']}"))
    current = chain[-1]
    if current["league_id"] == LEAGUE_ID:
        print(f"{LEAGUE_ID} ({league['season']}, {league['status']}) is the newest season; nothing to do")
        return 0
    for lg in chain[1:]:
        print(f"renewed: {lg['season']} -> {lg['league_id']} ({lg['name']}, {lg['status']})")
    if "--write" in sys.argv:
        CONFIG["sleeperLeagueId"] = current["league_id"]
        with open(CONFIG_PATH, "w") as f:
            f.write(json.dumps(CONFIG, indent=2, ensure_ascii=False) + "\n")
        print(f"league.json sleeperLeagueId -> {current['league_id']}. Re-run the data pipeline next.")
    else:
        print("run with --write to update league.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
