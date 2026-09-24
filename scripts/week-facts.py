#!/usr/bin/env python3
"""
The verified fact block for one week of the Mudd League.

Both blog editions -- the Monday in-progress report and the midweek preview -- need the same
arithmetic: what everyone scored, what they could have scored, what they left on the bench,
how they'd have done against the whole league, and where that ranks. This computes all of it
from live Sleeper data so a post never has to trust a number somebody typed by hand.

WHY THIS EXISTS AS A SCRIPT. On 2026-09-16 the Week 2 post called TnT44 the second-highest
scorer of Week 1. He was third. The figures had been computed correctly -- the week before,
from the Week 1 post, before Monday Night Football moved them. Ten claims in that post were
wrong for the same reason. Rankings are the trap: they are right when written and silently
wrong after one late game. Re-running this immediately before publishing is the fix, and the
whole point of it being one command rather than a page of ad-hoc Python.

Usage:
  python3 scripts/week-facts.py 1                  # current season, week 1
  python3 scripts/week-facts.py 1 --json           # machine-readable
  python3 scripts/week-facts.py 1 --fixture DIR    # derive from a saved snapshot, no network
  python3 scripts/week-facts.py --h2h Gurret Streinz
  python3 scripts/week-facts.py --history          # all-time leaderboards for fact checks
"""

import argparse
import json
import os
import sys
import urllib.request
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "static", "data")
LEAGUE_ID = "1312235880743706624"
API = "https://api.sleeper.app/v1"

FLEX_OK = {"RB", "WR", "TE"}


def get(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read())


def load(name):
    with open(os.path.join(DATA, name)) as f:
        return json.load(f)


HISTORY = load("league-history.json")
PLAYERS = load("players.json")
WEEKS = load("weeks.json")["weeks"]
MANAGERS = HISTORY["managers"]

# Team names are what the league calls each other in a post; handles are what the data uses.
TEAMS = {}
for uid, m in MANAGERS.items():
    TEAMS[uid] = m.get("handle", uid)


def handle(uid):
    return TEAMS.get(uid, str(uid))


def uid_for(name):
    """Resolve a handle, case-insensitively, to a user id."""
    for uid, h in TEAMS.items():
        if h.lower() == name.lower():
            return uid
    matches = [uid for uid, h in TEAMS.items() if name.lower() in h.lower()]
    if len(matches) == 1:
        return matches[0]
    raise SystemExit(f"could not resolve manager '{name}' (have: {', '.join(sorted(TEAMS.values()))})")


def position(pid, extra=None):
    p = PLAYERS.get(str(pid), {}).get("p")
    if p:
        return p
    if extra:
        return extra.get(str(pid), {}).get("position")
    return None


def player_name(pid, extra=None):
    n = PLAYERS.get(str(pid), {}).get("n")
    if n:
        return n
    if extra:
        return extra.get(str(pid), {}).get("full_name") or str(pid)
    return str(pid)


def starter_slots(season):
    """
    The league's starting lineup for that season, bench excluded.

    Read per-season rather than hardcoded: the roster shrank from 14 spots to 13 between 2025
    and 2026, and an optimal-lineup calculation that assumes the wrong shape is wrong quietly.
    """
    slots = HISTORY["seasons"].get(str(season), {}).get("roster_positions")
    if not slots:
        slots = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX", "BN"]
    return [s for s in slots if s not in ("BN", "IR", "TAXI")]


def best_lineup(points_by_player, slots, extra=None, ineligible=()):
    """
    Highest-scoring legal lineup, and what it leaves behind.

    Greedy by descending points into dedicated slots before FLEX. That is optimal here because
    every FLEX-eligible position also has a dedicated slot, so there is no player who can fill
    a slot that a higher-scoring player could not.

    `ineligible` must contain anyone on IR. They accrue points in `players_points` but cannot
    legally be started, so counting them inflates the optimal lineup and therefore the benched
    total -- which in a post that grades people publicly means accusing someone of leaving
    points on the bench that they were never allowed to play. BBrown16 had Alec Pierce on IR
    scoring 8.10 in Week 1 of 2026; including him overstated his benched points by 1.30 and
    cost him 1.4 points of efficiency.
    """
    pool = []
    for pid, pts in (points_by_player or {}).items():
        if str(pid) in ineligible:
            continue
        pos = position(pid, extra)
        if pos:
            pool.append((pts, str(pid), pos))
    pool.sort(reverse=True)

    used, chosen = set(), []
    for slot in slots:
        for pts, pid, pos in pool:
            if pid in used:
                continue
            ok = (pos in FLEX_OK) if slot == "FLEX" else (pos == slot)
            if ok:
                used.add(pid)
                chosen.append((pid, pts, pos, slot))
                break
    bench = [(pid, pts, pos) for pts, pid, pos in pool if pid not in used]
    return chosen, bench


def week_facts(season, week, fixture=None):
    """
    `fixture` reads matchups.json / rosters.json from a directory instead of calling Sleeper.

    Sleeper has no point-in-time endpoint -- /matchups/{week} always returns the week as it
    stands now -- so the only way to reproduce a mid-week state, or to test the Monday edition
    after the week has finished, is from a snapshot captured at the time. Also useful for
    backfilling: drop a saved response in a directory and derive against it offline.
    """
    if fixture:
        with open(os.path.join(fixture, "matchups.json")) as f:
            matchups = json.load(f)
        with open(os.path.join(fixture, "rosters.json")) as f:
            rosters = json.load(f)
    else:
        matchups = get(f"{API}/league/{LEAGUE_ID}/matchups/{week}")
        rosters = get(f"{API}/league/{LEAGUE_ID}/rosters")
    rid2uid = {r["roster_id"]: r.get("owner_id") for r in rosters}
    slots = starter_slots(season)

    extra = None
    unknown = [
        str(p)
        for e in matchups
        for p in (e.get("players") or [])
        if str(p) not in PLAYERS
    ]
    if unknown:
        # players.json only holds players who have appeared in league history, so in-season
        # rookies and new signings are missing. Fall back rather than printing a raw id.
        extra = get(f"{API}/players/nfl")

    reserve_by_roster = {
        r["roster_id"]: {str(p) for p in (r.get("reserve") or [])} for r in rosters
    }

    teams = {}
    for e in matchups:
        uid = rid2uid.get(e["roster_id"])
        name = handle(uid)
        pp = e.get("players_points") or {}
        starter_ids = [str(x) for x in (e.get("starters") or []) if str(x) != "0"]
        # A player who actually started was, by definition, eligible that week -- so he stays
        # in the optimal pool even if he is on IR today. `rosters` is a snapshot of NOW, not a
        # record of who could be started in a past week, and subtracting today's IR list from
        # a past week drops points that genuinely counted. TnT44 started Jordan Mason for 11.9
        # in Week 1 of 2026 and has him on IR since; excluding him retroactively produced an
        # optimal lineup BELOW what was actually scored, and a 103.3% efficiency.
        on_ir = reserve_by_roster.get(e["roster_id"], set()) - set(starter_ids)
        chosen, bench = best_lineup(pp, slots, extra, ineligible=on_ir)
        optimal = sum(p for _, p, _, _ in chosen)
        scored = e.get("points") or 0.0
        # The optimal lineup is the best lineup available, so it can never be worse than the
        # one actually played. If this trips, the eligibility filter has excluded somebody who
        # was genuinely startable and every benched/efficiency figure downstream is wrong.
        if optimal < scored - 0.001:
            raise SystemExit(
                f"optimal ({optimal:.2f}) below scored ({scored:.2f}) for {name} in week {week} "
                f"-- an eligible player is being filtered out of the optimal lineup"
            )
        yet_to_play = [
            player_name(pid, extra) for pid in starter_ids
            if (pp.get(pid) or 0) == 0
        ]

        # Efficiency judged only on the slots whose player has finished. A starter whose game
        # has not kicked off sits on 0.0, and best_lineup happily swaps him for any bench
        # player who has already scored -- charging the manager for a decision the week has
        # not finished making. In Week 2 of 2026 that hit five of ten teams, and all 11.00 of
        # tuckersdumbteam's "benched" was Xavier Worthy standing in for a receiver who had not
        # played yet. Here each pending starter keeps his slot and the rest are optimised over
        # players who have actually played. `starters` is index-aligned with the league's
        # starting slots, so the slot each pending player holds is known exactly rather than
        # guessed. Every 0.0 starter counts as pending, which carries the same ambiguity as
        # `starters_yet_to_play`: confirm against the NFL schedule before leaning on it.
        raw_starters = [str(x) for x in (e.get("starters") or [])]
        pending = {pid for pid in starter_ids if (pp.get(pid) or 0) == 0}
        open_slots = [slots[i] for i, pid in enumerate(raw_starters)
                      if i < len(slots) and pid not in pending]
        f_chosen, _ = best_lineup({k: v for k, v in pp.items() if str(k) not in pending},
                                  open_slots, extra, ineligible=on_ir | pending)
        f_optimal = sum(p for _, p, _, _ in f_chosen)
        f_scored = sum(pp.get(pid) or 0.0 for pid in starter_ids if pid not in pending)
        teams[name] = {
            "manager": name,
            "user_id": uid,
            "roster_id": e["roster_id"],
            "matchup_id": e.get("matchup_id"),
            "scored": round(scored, 2),
            "optimal": round(optimal, 2),
            "benched": round(optimal - scored, 2),
            "efficiency": round(scored / optimal * 100, 1) if optimal else None,
            "starters_yet_to_play": yet_to_play,
            # Use these, not benched/efficiency, for any team with a starter still to play.
            # With nobody pending they equal benched/efficiency exactly.
            "finished_benched": round(f_optimal - f_scored, 2),
            "finished_efficiency": round(f_scored / f_optimal * 100, 1) if f_optimal else None,
            # Not "players on the bench": these are the best players the OPTIMAL lineup left
            # out, which can include players who were actually started in the wrong slot.
            # Never write "X sat on his bench" from this list -- compare `started` with
            # `optimal_lineup` for that.
            "best_benched": sorted(
                ({"player": player_name(p, extra), "points": pts} for p, pts, _ in bench),
                key=lambda x: -x["points"],
            )[:3],
            # Who they ACTUALLY started, which is not the same list as the optimal lineup and
            # must never be confused with it -- writing "X started Y" off the optimal lineup
            # invents a decision nobody made. In Week 1 of 2026 the optimal lineup put Kyle
            # Pitts in tuckersdumbteam's tight end slot; he actually started Travis Kelce.
            "started": sorted(
                ({"player": player_name(p, extra), "points": pp.get(p) or 0.0}
                 for p in starter_ids),
                key=lambda x: -x["points"],
            ),
            "optimal_lineup": sorted(
                ({"player": player_name(p, extra), "points": pts, "slot": slot}
                 for p, pts, _, slot in chosen),
                key=lambda x: -x["points"],
            ),
        }

    order = sorted(teams.values(), key=lambda t: -t["scored"])
    for i, t in enumerate(order, 1):
        t["score_rank"] = i

    # All-play: the record each team would hold if it had played everyone. Separates being
    # beaten from being unlucky, which is most of what a weekly post argues about.
    for t in teams.values():
        w = sum(1 for o in teams.values() if o is not t and t["scored"] > o["scored"])
        l = sum(1 for o in teams.values() if o is not t and t["scored"] < o["scored"])
        t["all_play"] = f"{w}-{l}"

    games = []
    by_mid = defaultdict(list)
    for t in teams.values():
        by_mid[t["matchup_id"]].append(t)
    for mid, pair in sorted(by_mid.items(), key=lambda kv: kv[0] or 0):
        if len(pair) != 2:
            continue
        a, b = sorted(pair, key=lambda t: -t["scored"])
        games.append({
            "matchup_id": mid,
            "leader": a["manager"], "leader_points": a["scored"],
            "trailer": b["manager"], "trailer_points": b["scored"],
            "margin": round(a["scored"] - b["scored"], 2),
            # What the trailing team needs to win outright: strictly more than the margin,
            # which at two decimals means margin + 0.01.
            "trailer_needs": round(a["scored"] - b["scored"] + 0.01, 2),
            # A result can only still change if the TRAILING team has someone left. If only
            # the leader does, the game is decided and the leader is merely padding. Asking
            # "does anyone have a zero" instead flagged all five Week 1 games as live when
            # two were over -- and a zero is ambiguous anyway, since it equally means a
            # player who has finished and scored nothing.
            "trailer_can_still_win": bool(b["starters_yet_to_play"]),
            "leader_still_playing": bool(a["starters_yet_to_play"]),
            "trailer_yet_to_play": b["starters_yet_to_play"],
        })

    perf = []
    for t in teams.values():
        for s in t["started"]:
            perf.append({"player": s["player"], "points": s["points"], "manager": t["manager"]})
    perf.sort(key=lambda x: -x["points"])

    return {
        "season": str(season),
        "week": int(week),
        "teams": {k: v for k, v in sorted(teams.items(), key=lambda kv: -kv[1]["scored"])},
        "games": games,
        "top_performances": perf[:10],
        "rankings": {
            "by_score": [t["manager"] for t in order],
            "by_efficiency": [t["manager"] for t in sorted(teams.values(), key=lambda x: -(x["efficiency"] or 0))],
            "by_benched": [t["manager"] for t in sorted(teams.values(), key=lambda x: -x["benched"])],
            "by_optimal": [t["manager"] for t in sorted(teams.values(), key=lambda x: -x["optimal"])],
        },
    }


# ---------------------------------------------------------------------------------------
# History, for fact-checking superlatives
# ---------------------------------------------------------------------------------------

def season_played(season):
    """A scheduled-but-unplayed season returns full-looking weeks with every score 0.0."""
    return any(
        (row.get("points") or 0) > 0
        for rows in WEEKS.get(str(season), {}).values()
        for row in rows.values()
    )


def all_results():
    """Every completed fixture, 2022 onward, as (season, week, uid, points, opp_points)."""
    out = []
    for season in sorted(WEEKS):
        if not season_played(season):
            continue
        slots = starter_slots(season)
        for wk, rows in WEEKS[season].items():
            groups = defaultdict(list)
            for uid, row in rows.items():
                if row.get("matchup_id"):
                    groups[row["matchup_id"]].append((uid, row))
            for mid, pair in groups.items():
                if len(pair) != 2:
                    continue
                (ua, ra), (ub, rb) = pair
                pa, pb = ra.get("points") or 0, rb.get("points") or 0
                if pa == 0 and pb == 0:
                    continue
                for (u, r, mine, theirs) in ((ua, ra, pa, pb), (ub, rb, pb, pa)):
                    chosen, _ = best_lineup(r.get("players_points"), slots)
                    opt = sum(p for _, p, _, _ in chosen)
                    out.append({
                        "season": season, "week": int(wk), "uid": u, "manager": handle(u),
                        "points": round(mine, 2), "opponent_points": round(theirs, 2),
                        "won": mine > theirs, "optimal": round(opt, 2),
                        "benched": round(opt - mine, 2),
                    })
    return out


def history_report():
    res = all_results()
    def top(rows, key, n=5, reverse=True):
        return sorted(rows, key=lambda r: r[key], reverse=reverse)[:n]

    print("Seasons with completed games:", ", ".join(s for s in sorted(WEEKS) if season_played(s)))
    print("\nHIGHEST SCORES")
    for r in top(res, "points"):
        print(f"  {r['points']:7.2f}  {r['manager']:11s} {r['season']} wk{r['week']}")
    print("\nHIGHEST LOSING SCORES")
    for r in top([r for r in res if not r["won"]], "points"):
        print(f"  {r['points']:7.2f}  {r['manager']:11s} {r['season']} wk{r['week']} (lost to {r['opponent_points']})")
    print("\nLOWEST SCORES")
    for r in top(res, "points", reverse=False):
        print(f"  {r['points']:7.2f}  {r['manager']:11s} {r['season']} wk{r['week']}")
    print("\nMOST POINTS LEFT ON THE BENCH")
    for r in top(res, "benched"):
        print(f"  {r['benched']:7.2f}  {r['manager']:11s} {r['season']} wk{r['week']} (scored {r['points']}, optimal {r['optimal']})")
    print("\nCLOSEST FINISHES")
    margins = sorted(({"m": round(r["points"] - r["opponent_points"], 2), **r} for r in res if r["won"]), key=lambda x: x["m"])[:5]
    for r in margins:
        print(f"  {r['m']:7.2f}  {r['manager']:11s} {r['season']} wk{r['week']} ({r['points']} to {r['opponent_points']})")


def head_to_head(a, b):
    ua, ub = uid_for(a), uid_for(b)
    wa = wb = 0
    pa = pb = 0.0
    games = []
    for season in sorted(WEEKS):
        if not season_played(season):
            continue
        for wk, rows in WEEKS[season].items():
            ra, rb = rows.get(ua), rows.get(ub)
            if not ra or not rb:
                continue
            if not ra.get("matchup_id") or ra.get("matchup_id") != rb.get("matchup_id"):
                continue
            x, y = ra.get("points") or 0, rb.get("points") or 0
            if x == 0 and y == 0:
                continue
            pa += x
            pb += y
            games.append((season, int(wk), round(x, 2), round(y, 2)))
            if x > y:
                wa += 1
            elif y > x:
                wb += 1
    return {
        "a": handle(ua), "b": handle(ub), "meetings": len(games),
        "record": f"{wa}-{wb}", "points_a": round(pa, 2), "points_b": round(pb, 2),
        "point_diff": round(pa - pb, 2), "games": sorted(games),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("week", nargs="?", type=int)
    ap.add_argument("--season", default=None)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--live", action="store_true",
                    help="also list every team's starters yet to play, not just trailing teams")
    ap.add_argument("--h2h", nargs=2, metavar=("A", "B"))
    ap.add_argument("--history", action="store_true")
    ap.add_argument("--fixture", metavar="DIR",
                    help="read matchups.json/rosters.json from DIR instead of calling Sleeper")
    args = ap.parse_args()

    if args.history:
        history_report()
        return 0

    if args.h2h:
        r = head_to_head(*args.h2h)
        if args.json:
            print(json.dumps(r, indent=1))
        else:
            print(f"{r['a']} vs {r['b']}: {r['record']} in {r['meetings']} meetings")
            print(f"  points {r['points_a']} - {r['points_b']} (diff {r['point_diff']:+})")
            for s, wk, x, y in r["games"]:
                print(f"    {s} wk{wk}: {x} - {y}")
        return 0

    if args.week is None:
        ap.error("give a week number, or use --h2h / --history")

    season = args.season or (HISTORY.get("generated", "")[:4] if args.fixture
                             else get(f"{API}/state/nfl")["season"])
    f = week_facts(season, args.week, fixture=args.fixture)

    if args.json:
        print(json.dumps(f, indent=1))
        return 0

    print(f"=== {f['season']} WEEK {f['week']} ===\n")
    print(f"{'#':>2} {'manager':12s} {'scored':>7s} {'optimal':>8s} {'benched':>8s} {'eff':>6s} {'all-play':>9s}")
    for t in f["teams"].values():
        print(f"{t['score_rank']:2d} {t['manager']:12s} {t['scored']:7.2f} {t['optimal']:8.2f} "
              f"{t['benched']:8.2f} {str(t['efficiency'])+'%':>6s} {t['all_play']:>9s}")
    print("\nGAMES")
    for g in f["games"]:
        if g["trailer_can_still_win"]:
            state = "MAYBE LIVE -- confirm"
        elif g["leader_still_playing"]:
            state = "decided (leader padding)"
        else:
            state = "final"
        print(f"  {g['leader']:12s} {g['leader_points']:7.2f}  def.  {g['trailer']:12s} "
              f"{g['trailer_points']:7.2f}  (margin {g['margin']}, {state})")
        if g["trailer_can_still_win"]:
            print(f"      {g['trailer']} needs {g['trailer_needs']} from "
                  f"{', '.join(g['trailer_yet_to_play'])}")
            if g["leader_still_playing"]:
                # The printed number is only the floor: whatever the leader's pending players
                # score raises it. In Week 2 of 2026 malstol "needed 25.37 from Skattebo" while
                # Kyren Williams was still to play for paulslaats -- the real bar was Skattebo
                # beating Williams by 25.37.
                print(f"      ^ and {g['leader']} still has players to come, so that is the "
                      f"floor, not the target")
            print(f"      ^ verify these have not already played -- a 0.0 starter is equally "
                  f"someone who finished and scored nothing")
    print("\nTOP PERFORMANCES (started)")
    for p in f["top_performances"][:5]:
        print(f"  {p['points']:6.2f}  {p['player']:22s} {p['manager']}")
    if args.live:
        print("\nSTARTERS YET TO PLAY (scoring 0.0 -- verify against the NFL schedule)")
        for t in f["teams"].values():
            if t["starters_yet_to_play"]:
                print(f"  {t['manager']:12s} {', '.join(t['starters_yet_to_play'])}")
    pending = [t for t in f["teams"].values() if t["starters_yet_to_play"]]
    if pending:
        print("\nON FINISHED SLOTS -- publish these, not the table above, for teams with a "
              "starter still to play")
        for t in pending:
            print(f"  {t['manager']:12s} benched {t['finished_benched']:6.2f}   "
                  f"eff {str(t['finished_efficiency'])+'%':>6s}   "
                  f"(table above: {t['benched']:.2f}, {t['efficiency']}%)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
