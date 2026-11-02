#!/usr/bin/env python3
"""
The verified fact block for one week of ANY Sleeper league, read entirely from the live API.

`week-facts.py` is the Mudd League's version: it leans on the committed dataset in
static/data/ (official-score overrides, stat corrections, positional eligibility fixes, the
playoff brackets). This script needs none of that, so it works for a league that has no
dataset -- BPM Fantasy Football first -- at the cost of those Mudd-specific refinements. For
the Mudd League, keep using week-facts.py.

What it adds over week-facts.py: it knows who has actually played. A starter on 0.0 is
ambiguous -- not kicked off yet, on bye, inactive, or played and scored nothing -- and every
Mudd Monday post has had to resolve that by hand. Here each starter is classified from
Sleeper's own week data:

  pending   his NFL team has a projection this week but no player on it has recorded a game
  bye       his NFL team has no projections this week at all
  inactive  his team has played, he has no `gp` -- he did not dress
  played    he recorded a game (a 0.0 here is a real zero)

Run it before a game kicks off or after it ends: a player in a game IN PROGRESS has `gp` and
counts as played, so a mid-game run understates what is still to come.

Usage:
  python3 scripts/league-week.py --league bpm 8              # week 8 fact block
  python3 scripts/league-week.py --league bpm 8 --json
  python3 scripts/league-week.py --league bpm --history      # all-time leaderboards
  python3 scripts/league-week.py --league bpm --standings    # current season table
  python3 scripts/league-week.py --league bpm --h2h "Team A" "Team B"

`--league` takes a name from scripts/leagues.json or a raw Sleeper league ID.
"""

import argparse
import json
import os
import sys
import time
import urllib.request
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://api.sleeper.app/v1"
CACHE = os.path.join(ROOT, ".cache", "sleeper")
REGISTRY = os.path.join(ROOT, "scripts", "leagues.json")

# Positions each flex slot accepts. Anything else must match the slot exactly.
ELIGIBLE = {
    "FLEX": {"RB", "WR", "TE"},
    "SUPER_FLEX": {"QB", "RB", "WR", "TE"},
    "WRRB_FLEX": {"RB", "WR"},
    "REC_FLEX": {"WR", "TE"},
}
NOT_STARTING = {"BN", "IR", "TAXI"}
POS_ALIAS = {"FB": "RB"}


# ---------------------------------------------------------------------------------------
# Fetching
# ---------------------------------------------------------------------------------------

def get(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read())


def cached(name, url, max_age=None):
    """Fetch through a file cache. max_age None means forever (use only for final data)."""
    path = os.path.join(CACHE, name)
    if os.path.exists(path) and (max_age is None or time.time() - os.path.getmtime(path) < max_age):
        with open(path) as f:
            return json.load(f)
    data = get(url)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f)
    return data


_PLAYERS = None


def players():
    """The ~15MB player dictionary, refreshed when over 12 hours old."""
    global _PLAYERS
    if _PLAYERS is None:
        _PLAYERS = cached("players-nfl.json", f"{API}/players/nfl", max_age=12 * 3600)
    return _PLAYERS


def pname(pid):
    p = players().get(str(pid)) or {}
    return p.get("full_name") or (f"{p.get('team')} DEF" if p.get("position") == "DEF" else str(pid))


def pos(pid):
    p = players().get(str(pid)) or {}
    x = p.get("position")
    return POS_ALIAS.get(x, x)


def injury(pid):
    return (players().get(str(pid)) or {}).get("injury_status")


def nfl_team(pid):
    return (players().get(str(pid)) or {}).get("team")


def resolve_league(arg):
    with open(REGISTRY) as f:
        reg = {k: v for k, v in json.load(f).items() if not k.startswith("_")}
    if arg in reg:
        return reg[arg]["league_id"], reg[arg].get("names", "team"), reg[arg].get("name")
    for v in reg.values():
        if v["league_id"] == arg:
            return arg, v.get("names", "team"), v.get("name")
    if arg.isdigit():
        return arg, "team", None
    raise SystemExit(f"unknown league '{arg}' (have: {', '.join(reg)})")


class League:
    def __init__(self, arg):
        self.id, self.names, self.label = resolve_league(arg)
        self.info = get(f"{API}/league/{self.id}")
        self.season = self.info["season"]
        self.label = self.label or self.info.get("name")
        # Read live every run. A cached team name is how the BPM Week 2 2026 article called
        # three teams by names they had dropped.
        self.users = {u["user_id"]: u for u in get(f"{API}/league/{self.id}/users")}

    def handle(self, uid):
        u = self.users.get(uid) or {}
        return u.get("display_name") or str(uid)

    def name(self, uid, fallback=None):
        u = self.users.get(uid)
        if not u:
            return fallback or str(uid)
        team = (u.get("metadata") or {}).get("team_name")
        if self.names == "team" and team:
            return team
        return u.get("display_name") or str(uid)

    def slots(self, info=None):
        return [s for s in (info or self.info)["roster_positions"] if s not in NOT_STARTING]


# ---------------------------------------------------------------------------------------
# The week
# ---------------------------------------------------------------------------------------

def best_lineup(points, slots, ineligible=()):
    """
    Highest-scoring legal lineup. Dedicated slots fill first, then flex slots from the narrowest
    to the widest, each taking the best remaining eligible player. Because the flex sets nest
    (FLEX inside SUPER_FLEX) and every flex position also has a dedicated slot, greedy is optimal.
    """
    pool = sorted(((v or 0.0, str(k), pos(k)) for k, v in (points or {}).items()
                   if str(k) not in ineligible and pos(k)), reverse=True)
    order = sorted(range(len(slots)), key=lambda i: len(ELIGIBLE.get(slots[i], {slots[i]})))
    used, chosen = set(), []
    for i in order:
        ok = ELIGIBLE.get(slots[i], {slots[i]})
        for pts, pid, p in pool:
            if pid not in used and p in ok:
                used.add(pid)
                chosen.append((pid, pts, slots[i]))
                break
    bench = [(pid, pts) for pts, pid, _ in pool if pid not in used]
    return chosen, bench


def nfl_week_status(season, week):
    """Which NFL teams have played this week, and which have a game at all."""
    stats = get(f"{API}/stats/nfl/regular/{season}/{week}")
    proj = get(f"{API}/projections/nfl/regular/{season}/{week}")
    played = {nfl_team(pid) for pid, s in stats.items() if (s.get("gp") or 0) > 0 and nfl_team(pid)}
    scheduled = {nfl_team(pid) for pid, s in proj.items()
                 if (s.get("pts_half_ppr") or s.get("pts_ppr") or 0) > 0 and nfl_team(pid)} | played
    return stats, played, scheduled


def week_facts(L, week):
    season = L.season
    matchups = get(f"{API}/league/{L.id}/matchups/{week}")
    rosters = get(f"{API}/league/{L.id}/rosters")
    stats, played, scheduled = nfl_week_status(season, week)
    slots = L.slots()
    owner = {r["roster_id"]: r.get("owner_id") for r in rosters}
    reserve = {r["roster_id"]: {str(p) for p in (r.get("reserve") or [])} for r in rosters}

    def status(pid):
        t = nfl_team(pid)
        if not t:
            return "no team"
        if t not in scheduled:
            return "bye"
        if t not in played:
            return "pending"
        return "played" if (stats.get(str(pid), {}).get("gp") or 0) > 0 else "inactive"

    teams = {}
    for e in matchups:
        uid = owner.get(e["roster_id"])
        pp = {str(k): v for k, v in (e.get("players_points") or {}).items()}
        raw = [str(x) for x in (e.get("starters") or [])]
        starters = [p for p in raw if p != "0"]
        on_ir = reserve.get(e["roster_id"], set()) - set(starters)
        chosen, bench = best_lineup(pp, slots, ineligible=on_ir)
        optimal = sum(p for _, p, _ in chosen)
        computed = e.get("points") or 0.0
        official = e["custom_points"] if e.get("custom_points") is not None else computed

        st = {p: status(p) for p in starters}
        pending = {p for p in starters if st[p] == "pending"}
        bench_pending = [pname(p) for p in (e.get("players") or [])
                         if str(p) not in starters and status(str(p)) == "pending"]
        # Grade only finished slots: each pending starter keeps his slot, everyone else is
        # optimised over players whose games are over. Pending bench players sit on 0.0 and
        # so cannot be picked, which is the right answer until they play.
        open_slots = [slots[i] for i, p in enumerate(raw) if i < len(slots) and p not in pending]
        f_chosen, _ = best_lineup({k: v for k, v in pp.items() if k not in pending},
                                  open_slots, ineligible=on_ir | pending)
        f_opt = sum(p for _, p, _ in f_chosen)
        f_scored = sum(pp.get(p) or 0.0 for p in starters if p not in pending)

        slot_of = {p: (slots[i] if i < len(slots) else "?") for i, p in enumerate(raw)}
        name = L.name(uid)
        teams[name] = {
            "team": name,
            "handle": L.handle(uid),
            "user_id": uid,
            "roster_id": e["roster_id"],
            "matchup_id": e.get("matchup_id"),
            "scored": round(official, 2),
            "override": e.get("custom_points") is not None,
            "optimal": round(optimal, 2),
            "benched": round(optimal - computed, 2),
            "efficiency": round(computed / optimal * 100, 1) if optimal else None,
            "finished_benched": round(f_opt - f_scored, 2),
            "finished_efficiency": round(f_scored / f_opt * 100, 1) if f_opt else None,
            "yet_to_play": [pname(p) for p in starters if p in pending],
            # A pending starter Sleeper already lists as Out or Doubtful is probably not live
            # at all -- confirm against the team's game-day inactives before calling a game.
            "yet_to_play_flagged": [f"{pname(p)} ({injury(p)})" for p in starters
                                    if p in pending and injury(p) in ("Out", "Doubtful", "IR", "Sus")],
            "bench_yet_to_play": bench_pending,
            # Started and finished on zero, with the reason. "bye" and "inactive" are lineup
            # decisions; "played" is a real zero.
            "zero_starters": [{"player": pname(p), "why": st[p]} for p in starters
                              if p not in pending and not (pp.get(p) or 0)],
            "started": [{"player": pname(p), "slot": slot_of[p], "points": pp.get(p) or 0.0,
                         "status": st[p]} for p in starters],
            "optimal_lineup": sorted(({"player": pname(p), "slot": s, "points": v}
                                      for p, v, s in chosen), key=lambda x: -x["points"]),
            # NOT "players on the bench": the best players the optimal lineup left out.
            "best_benched": [{"player": pname(p), "points": v}
                             for p, v in sorted(bench, key=lambda b: -(b[1] or 0))[:3]],
        }

    order = sorted(teams.values(), key=lambda t: -t["scored"])
    for i, t in enumerate(order, 1):
        t["score_rank"] = i
    for t in teams.values():
        w = sum(1 for o in teams.values() if o is not t and t["scored"] > o["scored"])
        l = sum(1 for o in teams.values() if o is not t and t["scored"] < o["scored"])
        t["all_play"] = f"{w}-{l}"

    games = []
    by_mid = defaultdict(list)
    for t in teams.values():
        if t["matchup_id"]:
            by_mid[t["matchup_id"]].append(t)
    for mid, pair in sorted(by_mid.items()):
        if len(pair) != 2:
            continue
        a, b = sorted(pair, key=lambda t: -t["scored"])
        trailer_live, leader_live = bool(b["yet_to_play"]), bool(a["yet_to_play"])
        games.append({
            "matchup_id": mid,
            "leader": a["team"], "leader_points": a["scored"],
            "trailer": b["team"], "trailer_points": b["scored"],
            "margin": round(a["scored"] - b["scored"], 2),
            "trailer_needs": round(a["scored"] - b["scored"] + 0.01, 2),
            "state": "live" if trailer_live else ("decided, leader still playing" if leader_live else "final"),
            "trailer_yet_to_play": b["yet_to_play"],
            "trailer_flagged": b["yet_to_play_flagged"],
            "leader_yet_to_play": a["yet_to_play"],
        })

    perf = sorted(({"player": s["player"], "points": s["points"], "team": t["team"]}
                   for t in teams.values() for s in t["started"]), key=lambda x: -x["points"])
    return {
        "league": L.label, "season": season, "week": week,
        "nfl_teams_pending": sorted(scheduled - played),
        "nfl_teams_on_bye": sorted({nfl_team(p) for p, x in players().items() if nfl_team(p) and x.get("active")} - scheduled),
        "teams": {t["team"]: t for t in order},
        "games": games,
        "top_performances": perf[:10],
    }


# ---------------------------------------------------------------------------------------
# History: every completed regular-season game, walking previous_league_id back
# ---------------------------------------------------------------------------------------

def history(L):
    state = get(f"{API}/state/nfl")
    rows, seasons = [], []
    lid, info = L.id, L.info
    while lid and lid != "0":
        if info is None:
            info = cached(f"{lid}/league.json", f"{API}/league/{lid}")
        season = info["season"]
        current = info.get("status") != "complete"
        first_playoff = (info.get("settings") or {}).get("playoff_week_start") or 15
        last_reg = first_playoff - 1
        if current:
            if state["season"] != season:
                last = 0
            else:
                last = min(last_reg, int(state["week"]) - 1)
        else:
            last = last_reg
        r_age = 6 * 3600 if current else None
        rosters = cached(f"{lid}/rosters.json", f"{API}/league/{lid}/rosters", max_age=r_age)
        users = {u["user_id"]: u for u in cached(f"{lid}/users.json", f"{API}/league/{lid}/users", max_age=r_age)}
        owner = {r["roster_id"]: r.get("owner_id") for r in rosters}
        played_any = False
        for wk in range(1, last + 1):
            # The newest completed week can still take stat corrections, so it is re-fetched.
            fresh = not current or wk < last
            ms = cached(f"{lid}/matchups-{wk}.json", f"{API}/league/{lid}/matchups/{wk}",
                        max_age=None if fresh else 3600)
            if not any((m.get("points") or 0) > 0 for m in ms):
                continue  # scheduled but unplayed
            played_any = True
            pairs = defaultdict(list)
            for m in ms:
                if m.get("matchup_id"):
                    pairs[m["matchup_id"]].append(m)
            for pair in pairs.values():
                if len(pair) != 2:
                    continue
                for me, opp in (pair, pair[::-1]):
                    def off(x):
                        return x["custom_points"] if x.get("custom_points") is not None else (x.get("points") or 0.0)
                    u, o = owner.get(me["roster_id"]), owner.get(opp["roster_id"])
                    a, b = off(me), off(opp)
                    rows.append({"season": season, "week": wk, "uid": u, "opp": o,
                                 "points": round(a, 2), "opp_points": round(b, 2),
                                 "result": "W" if a > b else ("L" if a < b else "T"),
                                 "old_handle": (users.get(u) or {}).get("display_name"),
                                 "opp_old_handle": (users.get(o) or {}).get("display_name")})
        if played_any:
            seasons.append(season)
        lid, info = info.get("previous_league_id"), None
    return rows, sorted(seasons)


def label(L, r, key="uid"):
    """Current team name for a current manager; a departed manager's handle from that season."""
    return L.name(r[key], fallback=r.get("old_handle" if key == "uid" else "opp_old_handle"))


def history_report(L):
    rows, seasons = history(L)
    print(f"{L.label}: regular-season games only, seasons {', '.join(seasons)}; "
          f"{len(rows) // 2} games. Official scores (a commissioner override wins).")

    def show(title, rs, fmt):
        print(f"\n{title}")
        for r in rs:
            print("  " + fmt(r))

    s = lambda r: f"{r['points']:7.2f}  {label(L, r)} -- {r['season']} wk{r['week']}"
    show("HIGHEST SCORES", sorted(rows, key=lambda r: -r["points"])[:8], s)
    show("LOWEST SCORES", sorted(rows, key=lambda r: r["points"])[:8], s)
    show("HIGHEST LOSING SCORES", sorted((r for r in rows if r["result"] == "L"), key=lambda r: -r["points"])[:5],
         lambda r: s(r) + f" (lost to {r['opp_points']})")
    wins = [r for r in rows if r["result"] == "W"]
    show("CLOSEST FINISHES", sorted(wins, key=lambda r: r["points"] - r["opp_points"])[:8],
         lambda r: f"{r['points'] - r['opp_points']:7.2f}  {label(L, r)} over {label(L, r, 'opp')} "
                   f"-- {r['season']} wk{r['week']} ({r['points']} to {r['opp_points']})")
    show("BIGGEST MARGINS", sorted(wins, key=lambda r: -(r["points"] - r["opp_points"]))[:5],
         lambda r: f"{r['points'] - r['opp_points']:7.2f}  {label(L, r)} over {label(L, r, 'opp')} "
                   f"-- {r['season']} wk{r['week']}")

    # Streaks, across seasons, per manager (user id).
    by = defaultdict(list)
    for r in sorted(rows, key=lambda r: (r["season"], r["week"])):
        by[r["uid"]].append(r)
    longest = {"W": [], "L": []}
    current = []
    for uid, rs in by.items():
        run, kind, start = 0, None, None
        for r in rs:
            if r["result"] == kind:
                run += 1
            else:
                run, kind, start = 1, r["result"], r
            if kind in longest:
                longest[kind].append((run, label(L, r), start["season"], start["week"], r["season"], r["week"]))
        if uid in L.users:  # a departed manager's last run is not a current one
            current.append((run, kind, label(L, rs[-1])))
    for k, title in (("W", "LONGEST WINNING RUNS"), ("L", "LONGEST LOSING RUNS")):
        best = {}
        for x in longest[k]:
            key = (x[1], x[2], x[3])
            best[key] = max(best.get(key, x), x)
        show(title, sorted(best.values(), reverse=True)[:5],
             lambda x: f"{x[0]:3d}  {x[1]} ({x[2]} wk{x[3]} to {x[4]} wk{x[5]})")
    show("CURRENT RUNS", sorted(current, key=lambda x: (-x[0], x[2]))[:16],
         lambda x: f"{x[0]:3d} {x[1]}  {x[2]}")

    # Season-opening runs, the "worst start ever" check.
    opens = []
    for (uid, season), rs in group_season(rows).items():
        n = 0
        for r in rs:
            if r["result"] != "L":
                break
            n += 1
        w = 0
        for r in rs:
            if r["result"] != "W":
                break
            w += 1
        opens.append((n, w, label(L, rs[0]), season, len(rs)))
    show("WORST SEASON STARTS (opening losses)", sorted(opens, key=lambda x: -x[0])[:5],
         lambda x: f"0-{x[0]}  {x[2]} {x[3]} (of {x[4]} games played)")
    show("BEST SEASON STARTS (opening wins)", sorted(opens, key=lambda x: -x[1])[:5],
         lambda x: f"{x[1]}-0  {x[2]} {x[3]} (of {x[4]} games played)")


def group_season(rows):
    out = defaultdict(list)
    for r in sorted(rows, key=lambda r: (r["season"], r["week"])):
        out[(r["uid"], r["season"])].append(r)
    return out


def standings(L):
    rows, _ = history(L)
    table = defaultdict(lambda: {"W": 0, "L": 0, "T": 0, "PF": 0.0, "PA": 0.0})
    weeks = set()
    for r in rows:
        if r["season"] != L.season:
            continue
        weeks.add(r["week"])
        t = table[r["uid"]]
        t[r["result"]] += 1
        t["PF"] += r["points"]
        t["PA"] += r["opp_points"]
    print(f"{L.label} {L.season}, through week {max(weeks) if weeks else 0} (completed weeks only)")
    for i, (uid, t) in enumerate(sorted(table.items(), key=lambda kv: (-kv[1]["W"] - kv[1]["T"] / 2, -kv[1]["PF"])), 1):
        tie = f"-{t['T']}" if t["T"] else ""
        print(f"{i:2d} {L.name(uid):32s} {t['W']}-{t['L']}{tie}  PF {t['PF']:8.2f}  PA {t['PA']:8.2f}  ({L.handle(uid)})")


def resolve_team(L, rows, name):
    """A current team name or handle, case-insensitive, exact first, then a unique substring."""
    cands = {}
    for uid in {r["uid"] for r in rows} | set(L.users):
        for n in {L.name(uid), L.handle(uid)}:
            cands.setdefault(n.lower(), set()).add(uid)
    if name.lower() in cands and len(cands[name.lower()]) == 1:
        return next(iter(cands[name.lower()]))
    hits = {u for n, us in cands.items() if name.lower() in n for u in us}
    if len(hits) == 1:
        return hits.pop()
    raise SystemExit(f"'{name}' matches {len(hits)} teams; be more specific")


def head_to_head(L, a, b):
    rows, _ = history(L)
    ua, ub = resolve_team(L, rows, a), resolve_team(L, rows, b)
    games = [r for r in sorted(rows, key=lambda r: (r["season"], r["week"])) if r["uid"] == ua and r["opp"] == ub]
    w = sum(r["result"] == "W" for r in games)
    l = sum(r["result"] == "L" for r in games)
    pa = sum(r["points"] for r in games)
    pb = sum(r["opp_points"] for r in games)
    print(f"{L.name(ua)} vs {L.name(ub)}: {w}-{l} in {len(games)} regular-season meetings "
          f"(record is the first team's)")
    print(f"  points {pa:.2f} - {pb:.2f} (diff {pa - pb:+.2f})")
    for r in games:
        print(f"    {r['season']} wk{r['week']}: {r['points']} - {r['opp_points']}")


# ---------------------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("week", nargs="?", type=int)
    ap.add_argument("--league", required=True, help="name in scripts/leagues.json, or a league ID")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--history", action="store_true")
    ap.add_argument("--standings", action="store_true")
    ap.add_argument("--h2h", nargs=2, metavar=("A", "B"))
    args = ap.parse_args()
    L = League(args.league)

    if args.history:
        history_report(L)
        return 0
    if args.standings:
        standings(L)
        return 0
    if args.h2h:
        head_to_head(L, *args.h2h)
        return 0
    if args.week is None:
        ap.error("give a week number, or use --history / --standings / --h2h")

    f = week_facts(L, args.week)
    if args.json:
        print(json.dumps(f, indent=1))
        return 0

    w = max(len(t) for t in f["teams"]) + 1
    print(f"=== {f['league']} -- {f['season']} WEEK {f['week']} ===")
    print(f"NFL teams still to play: {', '.join(f['nfl_teams_pending']) or 'none'}")
    print(f"NFL teams on bye:        {', '.join(f['nfl_teams_on_bye']) or 'none'}\n")
    print(f"{'#':>2} {'team':{w}s} {'scored':>7s} {'benched':>8s} {'eff':>6s} {'fin.bench':>9s} {'fin.eff':>7s} {'all-play':>8s}")
    for t in f["teams"].values():
        print(f"{t['score_rank']:2d} {t['team']:{w}s} {t['scored']:7.2f} {t['benched']:8.2f} "
              f"{str(t['efficiency']) + '%':>6s} {t['finished_benched']:9.2f} "
              f"{str(t['finished_efficiency']) + '%':>7s} {t['all_play']:>8s}")
    print("  (fin.* grade finished slots only -- publish those for any team with a starter to come)")

    print("\nGAMES")
    for g in f["games"]:
        print(f"  {g['leader']} {g['leader_points']:.2f}  v  {g['trailer']} {g['trailer_points']:.2f}"
              f"  -- margin {g['margin']}, {g['state'].upper()}")
        if g["state"] == "live":
            extra = (f"; and the leader still has {', '.join(g['leader_yet_to_play'])}, so it is a floor"
                     if g["leader_yet_to_play"] else "; exact, the leader is finished")
            print(f"      trailer needs {g['trailer_needs']} from {', '.join(g['trailer_yet_to_play'])}{extra}")
            if g["trailer_flagged"]:
                print(f"      ^ Sleeper injury status: {', '.join(g['trailer_flagged'])} -- check inactives")
        elif g["leader_yet_to_play"]:
            print(f"      leader still has {', '.join(g['leader_yet_to_play'])} (a negative score could still flip it)")

    print("\nSTARTED AND SCORED ZERO (finished)")
    for t in f["teams"].values():
        for z in t["zero_starters"]:
            print(f"  {t['team']}: {z['player']} -- {z['why']}")
    print("\nTOP PERFORMANCES (started)")
    for p in f["top_performances"][:6]:
        print(f"  {p['points']:6.2f}  {p['player']:24s} {p['team']}")
    print("\nSTILL TO PLAY")
    for t in f["teams"].values():
        if t["yet_to_play"] or t["bench_yet_to_play"]:
            print(f"  {t['team']}: starting {', '.join(t['yet_to_play']) or '-'}"
                  f" | bench {', '.join(t['bench_yet_to_play']) or '-'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
