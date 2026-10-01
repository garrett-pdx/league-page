#!/usr/bin/env python3
"""
Sleeper's weekly projections, scored with THIS league's settings.

  python3 scripts/projections.py 3 "Joe Burrow" "Jalen Hurts"
  python3 scripts/projections.py 3 "Brian Thomas" "Kenyon Sadiq"

This is the yardstick for "was that start/sit call defensible?": what the platform the league
plays on projected for each player *that week*, which is what the manager was looking at when
he set the lineup. A preseason trade-value rank is the wrong yardstick -- "ranked 48th in
August" says nothing about a Week 3 matchup -- and the posts stopped citing one.

Sleeper's own `pts_half_ppr` uses generic scoring (four-point passing touchdowns); this league
gives six. So projected points here are recomputed from the projected stat lines against the
league's `scoring_settings`, the same way Sleeper scores actual games. The script checks that
recipe against reality on every run: it scores each player's ACTUAL stat line the same way and
prints it beside the points the league actually credited. If those two columns disagree, the
scoring recipe is wrong and the projections can't be trusted either.

Also prints each player's projected rank at his position that week (QB12, TE7, ...), which
reads better in a post than a raw projection.

Sleeper does not document whether a past week's projection is frozen at kickoff, so we keep
our own copy:

  python3 scripts/projections.py 4 --snapshot

saves that week's projections to static/data/projections/<season>-w<week>.json, stamped with
the capture time. Take it in the midweek run, before Thursday kickoff, and commit it. Lookups
for a week with a snapshot read the snapshot, and also report any player whose live projection
has since changed -- which is how we find out whether Sleeper rewrites old weeks.
"""
import datetime
import json
import os
import sys
import urllib.request

API = "https://api.sleeper.app/v1"
LEAGUE_ID = "1312235880743706624"
SNAP_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "data", "projections")
POSITIONS = {"QB", "RB", "WR", "TE"}


def get(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.load(r)


def score(line, settings):
    return round(sum(v * settings[k] for k, v in (line or {}).items()
                     if k in settings and isinstance(v, (int, float))), 2)


def snapshot_path(season, week):
    return os.path.join(SNAP_DIR, f"{season}-w{week}.json")


def main():
    args = [a for a in sys.argv[1:] if a != "--snapshot"]
    if not args:
        sys.exit('usage: python3 scripts/projections.py <week> ["Player Name" ...] [--snapshot]')
    week, names = int(args[0]), args[1:]
    league = get(f"{API}/league/{LEAGUE_ID}")
    season, settings = league["season"], league["scoring_settings"]
    players = get(f"{API}/players/nfl")
    live = get(f"{API}/projections/nfl/regular/{season}/{week}")
    keys = set(settings)

    if "--snapshot" in sys.argv:
        # Only fantasy-relevant players, and only the stat keys the league scores, so the file
        # stays small enough to commit every week.
        keep = {pid: {k: v for k, v in line.items() if k in keys}
                for pid, line in live.items()
                if (players.get(pid) or {}).get("position") in POSITIONS
                and (players.get(pid) or {}).get("team") and score(line, settings) > 0}
        os.makedirs(SNAP_DIR, exist_ok=True)
        out = snapshot_path(season, week)
        with open(out, "w") as f:
            json.dump({"season": season, "week": week,
                       "captured_at": datetime.datetime.now().astimezone().isoformat(timespec="minutes"),
                       "source": f"{API}/projections/nfl/regular/{season}/{week}",
                       "players": keep}, f, separators=(",", ":"))
        print(f"saved {len(keep)} projections to {os.path.relpath(out)}")
        if not names:
            return

    snap_file = snapshot_path(season, week)
    if os.path.exists(snap_file):
        snap = json.load(open(snap_file))
        proj, source = snap["players"], f"snapshot captured {snap['captured_at']}"
    else:
        proj, source = live, "live endpoint (no snapshot for this week)"
    stats = get(f"{API}/stats/nfl/regular/{season}/{week}")
    actual = {}
    for m in get(f"{API}/league/{LEAGUE_ID}/matchups/{week}"):
        actual.update({str(k): v for k, v in (m.get("players_points") or {}).items()})

    # Positional rank: every player at the position with a projection, league-scored.
    by_pos = {}
    for pid, line in proj.items():
        p = players.get(pid) or {}
        if p.get("team") and p.get("position") in POSITIONS:
            by_pos.setdefault(p["position"], []).append((score(line, settings), pid))
    rank = {}
    for pos, rows in by_pos.items():
        for i, (_, pid) in enumerate(sorted(rows, reverse=True), 1):
            rank[pid] = f"{pos}{i}"

    print(f"{season} week {week} -- Sleeper projections, league scoring ({source})")
    print(f"{'player':22s} {'proj':>6s} {'rank':>6s}   {'actual':>7s} {'(check)':>8s}")
    for n in names:
        ids = [pid for pid, p in players.items() if p.get("full_name") == n and p.get("team")]
        if not ids:
            print(f"{n:22s} not found")
            continue
        pid = ids[0]
        p_pts = score(proj.get(pid), settings)
        a_rec = actual.get(pid)
        a_calc = score(stats.get(pid), settings)
        flag = "" if a_rec is None or abs(a_calc - a_rec) < 0.05 else "  <-- scoring recipe mismatch"
        drift = score(live.get(pid), settings)
        if os.path.exists(snap_file) and abs(drift - p_pts) >= 0.01:
            flag += f"  (live projection now {drift:.2f}: Sleeper has changed it since the snapshot)"
        print(f"{n:22s} {p_pts:6.2f} {rank.get(pid, '-'):>6s}   "
              f"{'-' if a_rec is None else f'{a_rec:7.2f}':>7s} {a_calc:8.2f}{flag}")


if __name__ == "__main__":
    main()
