#!/usr/bin/env python3
"""
Build the two small files the site's history pages fetch, from the big committed dataset.

    static/data/games.json          one row per team per game, every completed week
    static/data/season-notes.json   per-season facts league-history.json lacks

weeks.json is 370 KB and carries three traps that have each produced a wrong fact in this
repo (the fictional week 18, unplayed weeks that look real, playoff games told apart by week
number). Every page that needs results -- Schedule luck, the head-to-head grid, the Seasons
archive, Stat Lab -- reads games.json instead, so the traps are handled once, here, and the
pages cannot disagree with each other. season-notes.json exists so the 320 KB
transactions.json never ships to a browser.

Self-checks run before anything is written, and the script exits non-zero if one fails:

    1. Each manager's regular-season wins, losses, ties, points for and points against match
       league-history.json -> managers.*.records exactly.
    2. Every regular-season week has exactly teams/2 games, and every game appears twice,
       once from each side, with mirrored scores and results.
    3. max_pf (best legal lineup) is rebuilt per manager-season the way Sleeper builds its own
       potential_points (sleeper_potential(), a slot-order greedy) and must reproduce it to
       the cent, after the pinned stat corrections. Any manager-season that doesn't fails the
       script. The column written to games.json is the TRUE best lineup -- the same figure
       except in the two weeks where Sleeper's greedy sits below the optimum -- and it is null
       on a commissioner-override game. Every non-override row must also have max_pf >= the
       computed score.

Run:  python3 scripts/derive-site-data.py      (or: npm run derive-site-data)
Reads only committed files. No network, no Sleeper calls. Run it after
scripts/pull-league-history.py.
"""

import gzip
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from itertools import product

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "static", "data")

KINDS = ["regular", "playoff", "placement", "consolation"]

# Post-settlement stat corrections, pinned to the cent.
#
# Sleeper recomputes a week's matchup scores from current stats every time it is asked, but a
# roster's season points were settled at the time. When a stat is corrected after a week has
# settled, the two drift apart, and games.json -- built from the weekly scores -- cannot match
# league-history.json's season totals. These are the manager-seasons where that happened, each
# with the exact difference (games.json minus Sleeper's season figure). None changes a result:
# the closest affected game was won by 10.50.
#
# Pinned rather than tolerated, so the check stays exact: a NEW discrepancy anywhere still
# fails, and so does one of these moving by a cent. If a fresh one appears, find the game (a PF
# gap for one manager and the same PA gap for his opponent), confirm the result is unaffected,
# and add it here.
STAT_CORRECTIONS = {
    # 2023: jonahcartwright v Gurret (weeks 5 and 14) -- jonah's weekly scores sum 2.00 lower
    ("2023", "612407006212468736"): {"pf": -2.0},
    ("2023", "76909640692416512"): {"pa": -2.0},
    # 2024: Kabroa v tuckersdumbteam (weeks 4 and 13) -- Kabroa's sum 1.00 higher
    ("2024", "611649934390870016"): {"pf": 1.0},
    ("2024", "611664340277383168"): {"pa": 1.0},
}

# Sleeper stores season points as an integer plus hundredths and rounds each week before
# summing, so a season total can sit one cent off the sum of its weeks (BBrown16, 2023:
# 1453.00 v 1452.99). Anything bigger than a cent is a real discrepancy.
CENT = 0.0101

# FLEX takes RB/WR/TE. One fullback exists in the player set; treat him as a running back.
FLEX_OK = {"RB", "WR", "TE"}
POS_ALIAS = {"FB": "RB"}

# Positions Sleeper actually allowed, where players.json (today's primary position only) is
# wrong. Each entry was fitted to Sleeper's own season potential_points and reproduces it to the
# cent; check_max_pf() re-proves that on every run. Lives here, the lower layer, because
# derive-narratives.py imports this module and uses the same table.
#
#   Taysom Hill (4381): TE in 2022 (TE alone is exact; QB/TE is 0.96 over). QB/TE from 2023.
#       Sleeper's potential_points fills slots in order, QB first, so in a week Hill outscored
#       TnT44's quarterback it put Hill at QB and benched the quarterback -- 2023 week 9 and
#       2024 week 11. That is Sleeper's figure, not the best lineup: in 2024 week 11 TnT44
#       actually started Hill at TE (37.52) and his QB, and scored 140.88, above Sleeper's
#       125.82 "potential". best_lineup() takes the best of every eligible assignment.
#   Travis Hunter (12530): WR in 2025. players.json says DB, which has no slot; paulslaats
#       started him three times.
ELIGIBILITY = {
    ("2022", "4381"): {"TE"},
    ("2023", "4381"): {"QB", "TE"},
    ("2024", "4381"): {"QB", "TE"},
    ("2025", "4381"): {"QB", "TE"},
    ("2025", "12530"): {"WR"},
}


def load(name):
    with open(os.path.join(DATA, name)) as f:
        return json.load(f)


WEEKS = load("weeks.json")["weeks"]
HISTORY = load("league-history.json")
TRANSACTIONS = load("transactions.json")["transactions"]
PLAYERS = load("players.json")

MANAGERS = HISTORY["managers"]
SEASONS = HISTORY["seasons"]
BRACKETS = HISTORY.get("brackets", {})
NFL_STATE = HISTORY.get("nfl_state")

FAILURES = []


def fail(msg):
    FAILURES.append(msg)


def handle(user_id):
    return MANAGERS.get(user_id, {}).get("handle", user_id)


def r2(x):
    return round(x + 0.0, 2)


def player(pid):
    p = PLAYERS.get(str(pid), {})
    return {"id": str(pid), "name": p.get("n") or f"player {pid}", "pos": p.get("p")}


def position(pid):
    raw = PLAYERS.get(str(pid), {}).get("p")
    return POS_ALIAS.get(raw, raw)


# --------------------------------------------------------------------------------------
# Which weeks count
# --------------------------------------------------------------------------------------

def has_matchup(row):
    """
    Sleeper writes matchup_id 0 or null, never a real id, for a week that is not a fixture.

    Every season carries a week 18 in which all ten teams sit at matchup_id 0 (2022: null) and
    nobody sets a lineup; teams outside both playoff brackets sit at null in weeks 16-17 too.
    Same rule as has_matchup() in derive-narratives.py: falsy means "no fixture".
    """
    return bool(row.get("matchup_id"))


def week_complete(season, week):
    """
    Is this week over? The pull already writes completed weeks only (see completed_weeks() in
    pull-league-history.py), but this script must not trust an older weeks.json that predates
    that fix, which listed every scheduled 2026 week at 0.0. So the rule is applied again,
    week by week, from the nfl_state the pull recorded:

      - a finished season: every week;
      - the season in progress: weeks before the current NFL week.

    season_played() in derive-narratives.py only asks the question of a whole season, which is
    not enough: a half-played week has real points in it. And a week must have had a point
    scored in it at all.
    """
    rows = WEEKS.get(season, {}).get(str(week), {})
    if not any((r.get("points") or 0) > 0 for r in rows.values()):
        return False
    if week not in SEASONS.get(season, {}).get("weeks_played", []):
        return False
    if SEASONS[season].get("status") == "complete":
        return True
    if not NFL_STATE:
        raise SystemExit(f"{season} is not complete and league-history.json has no nfl_state -- "
                         f"re-run scripts/pull-league-history.py so the in-progress week is known")
    if int(season) < int(NFL_STATE["season"]):
        return True
    if int(season) > int(NFL_STATE["season"]):
        return False
    if NFL_STATE["season_type"] == "regular":
        return week < NFL_STATE["week"]
    return NFL_STATE["season_type"] == "post"


def league_weeks(season):
    """Completed weeks with at least one real fixture, ascending."""
    return sorted(
        (int(w) for w, rows in WEEKS[season].items()
         if any(has_matchup(r) for r in rows.values()) and week_complete(season, int(w))),
    )


# --------------------------------------------------------------------------------------
# Optimal lineup
# --------------------------------------------------------------------------------------

def starter_slots(season):
    """
    The starting lineup for that season, bench excluded. Read per season: the roster went from
    14 spots to 13 between 2025 and 2026, and a hardcoded shape is wrong quietly.
    """
    slots = SEASONS.get(season, {}).get("roster_positions") or []
    return [s for s in slots if s not in ("BN", "IR", "TAXI")]


def eligible(season, pid):
    """The slot-relevant positions a player could fill that season."""
    pid = str(pid)
    if (season, pid) in ELIGIBILITY:
        return ELIGIBILITY[(season, pid)]
    pos = position(pid)
    return {pos} if pos else set()


def greedy(row, slots, elig):
    """
    Sort the roster by points and fill the slots in roster order (dedicated slots before FLEX),
    each with the best unused player who can play it; `elig(pid)` gives the SET of positions he
    may fill. With one position per player this is exact, because every FLEX-eligible position
    also has its own dedicated slot, so no player can fill a slot that a higher scorer could
    not (the argument behind best_lineup() in week-facts.py). With a multi-position player it
    is what Sleeper computes, not the optimum.

    weeks.json does not record who was on IR that week, and Sleeper lists IR players in
    `players`, so they are in the pool here although they could not be started. Sleeper's own
    potential_points has the same pool, which is why the check against it can be exact.
    """
    pool = sorted(
        ((pts, str(pid), elig(pid)) for pid, pts in (row.get("players_points") or {}).items()),
        key=lambda x: (-x[0], x[1]),
    )
    used, total = set(), 0.0
    for slot in slots:
        for pts, pid, e in pool:
            if pid in used or not e:
                continue
            if (e & FLEX_OK) if slot == "FLEX" else (slot in e):
                used.add(pid)
                total += pts
                break
    return total


def optimal_points(row, slots):
    """Greedy on players.json positions alone, with no ELIGIBILITY overrides."""
    return greedy(row, slots, lambda pid: {position(pid)} if position(pid) else set())


def sleeper_potential(season, row):
    """Sleeper's own per-week potential points, as reproduced by check_max_pf()."""
    return greedy(row, starter_slots(season), lambda p: eligible(season, p))


def best_lineup(season, row):
    """
    The true best legal lineup: the greedy run once per single-position assignment of any
    multi-position player (Taysom Hill), keeping the best. Exact, and >= sleeper_potential().
    """
    slots = starter_slots(season)
    multi = [str(p) for p in (row.get("players_points") or {}) if len(eligible(season, p)) > 1]
    if not multi:
        return sleeper_potential(season, row)
    best = 0.0
    for choice in product(*(sorted(eligible(season, p)) for p in multi)):
        fixed = dict(zip(multi, choice))
        best = max(best, greedy(row, slots,
                                lambda p: {fixed[str(p)]} if str(p) in fixed else eligible(season, p)))
    return best


# --------------------------------------------------------------------------------------
# Games
# --------------------------------------------------------------------------------------

def roster_map(season):
    """roster_id -> user_id for ONE season. Roster IDs are meaningless across seasons."""
    out = {}
    for uid, m in MANAGERS.items():
        rec = m.get("records", {}).get(season)
        if not rec:
            continue
        rid = rec["roster_id"]
        if rid in out:
            raise SystemExit(f"{season}: roster_id {rid} maps to two managers "
                             f"({out[rid]} and {uid}) -- cannot resolve the bracket")
        out[rid] = uid
    return out


def bracket_kinds(season):
    """
    {(week, frozenset({user_a, user_b})): kind} for every decided bracket game.

    Taken from the brackets, never from the week number. Round r is played in week
    playoff_week_start + r - 1. Sleeper marks placement games with `p`:

      winners bracket, no p (semifinals) or p=1 (the final)   -> "playoff"
      winners bracket, p=3 (third-place game)                 -> "placement"
      losers bracket, any game (it decides 5th-8th here)      -> "consolation"

    Bracket rows carry roster IDs, mapped through that season's own roster map.
    """
    start = SEASONS[season].get("playoff_week_start")
    r2u = roster_map(season)
    out = {}
    for side in ("winners", "losers"):
        for g in BRACKETS.get(season, {}).get(side) or []:
            if g.get("t1") is None or g.get("t2") is None or not g.get("r"):
                continue
            if side == "winners":
                kind = "placement" if g.get("p") == 3 else "playoff"
            else:
                kind = "consolation"
            a, b = r2u.get(g["t1"]), r2u.get(g["t2"])
            if not a or not b:
                fail(f"{season} {side} bracket game m={g.get('m')}: roster "
                     f"{g['t1']} or {g['t2']} has no manager that season")
                continue
            out[(start + g["r"] - 1, frozenset((a, b)))] = kind
    return out


def official_points(row):
    """
    The score that counted. A commissioner override (`custom_points`, kept by the pull only
    where set) beats the computed `points`; Sleeper's records and season totals use it. One
    case so far: 2024 week 8, tuckersdumbteam v BBrown16.
    """
    if row.get("custom_points") is not None:
        return r2(row["custom_points"])
    return r2(row.get("points") or 0)


def build_games():
    """One dict per team per game, completed weeks only."""
    games = []
    for season in sorted(WEEKS, key=int):
        weeks = league_weeks(season)
        if not weeks:
            continue
        start = SEASONS[season].get("playoff_week_start")
        kinds = bracket_kinds(season)
        r2u = roster_map(season)
        found_bracket = set()
        for week in weeks:
            rows = WEEKS[season][str(week)]
            by_id = defaultdict(list)
            for uid, row in rows.items():
                if r2u.get(row.get("roster_id")) != uid:
                    fail(f"{season} wk{week}: weeks.json has {handle(uid)} on roster "
                         f"{row.get('roster_id')}, records say otherwise")
                if has_matchup(row):
                    by_id[row["matchup_id"]].append((uid, row))
            for mid, pair in sorted(by_id.items()):
                if len(pair) != 2:
                    fail(f"{season} wk{week} matchup {mid}: {len(pair)} teams, expected 2")
                    continue
                if week < start:
                    kind = "regular"
                else:
                    key = (week, frozenset(u for u, _ in pair))
                    kind = kinds.get(key)
                    if not kind:
                        fail(f"{season} wk{week}: {handle(pair[0][0])} v {handle(pair[1][0])} is a "
                             f"playoff-week fixture with no bracket game")
                        continue
                    found_bracket.add(key)
                for (uid, row), (opp, orow) in ((pair[0], pair[1]), (pair[1], pair[0])):
                    pf, pa = official_points(row), official_points(orow)
                    # pf is the official score, max_pf is computed from player points: on a
                    # commissioner-override row the two are not comparable, so max_pf is null
                    # there instead of a number that would imply a bench total.
                    overridden = row.get("custom_points") is not None
                    games.append({
                        "season": int(season), "week": week, "user_id": uid, "opponent_id": opp,
                        "pf": pf, "pa": pa,
                        "result": "W" if pf > pa else "L" if pf < pa else "T",
                        "kind": kind,
                        "max_pf": None if overridden else r2(best_lineup(season, row)),
                        # Not written to games.json. Kept for the self-checks: Sleeper's figure
                        # for the week, and the computed (pre-override) score.
                        "potential": sleeper_potential(season, row),
                        "computed": r2(row.get("points") or 0),
                    })
        # The reverse direction: a bracket game in a completed week that never turned up.
        for key in kinds:
            if key[0] in weeks and key not in found_bracket:
                a, b = sorted(key[1])
                fail(f"{season} wk{key[0]}: bracket game {handle(a)} v {handle(b)} "
                     f"missing from weeks.json")
    games.sort(key=lambda g: (g["season"], g["week"], g["user_id"]))
    return games


# --------------------------------------------------------------------------------------
# Self-checks
# --------------------------------------------------------------------------------------

def check_records(games):
    """Regular-season W/L/T and points, per manager-season, against Sleeper's roster records."""
    tally = defaultdict(lambda: {"wins": 0, "losses": 0, "ties": 0, "pf": 0.0, "pa": 0.0})
    for g in games:
        if g["kind"] != "regular":
            continue
        t = tally[(str(g["season"]), g["user_id"])]
        t[{"W": "wins", "L": "losses", "T": "ties"}[g["result"]]] += 1
        t["pf"] += g["pf"]
        t["pa"] += g["pa"]

    seasons = {str(g["season"]) for g in games}
    checked = 0
    for uid, m in MANAGERS.items():
        for season, rec in m.get("records", {}).items():
            if season not in seasons:
                continue
            t = tally.get((season, uid), {"wins": 0, "losses": 0, "ties": 0, "pf": 0.0, "pa": 0.0})
            mine = (t["wins"], t["losses"], t["ties"], r2(t["pf"]), r2(t["pa"]))
            theirs = (rec["wins"] or 0, rec["losses"] or 0, rec["ties"] or 0,
                      r2(rec["points_for"]), r2(rec["points_against"]))
            pinned = STAT_CORRECTIONS.get((season, uid), {})
            points_ok = all(
                abs(mine[i] - theirs[i] - pinned.get(key, 0.0)) <= CENT
                for i, key in ((3, "pf"), (4, "pa"))
            )
            checked += 1
            if mine[:3] != theirs[:3] or not points_ok:
                hint = ""
                if season == (NFL_STATE or {}).get("season"):
                    hint = (" -- the in-progress season; if Sleeper has just finalised a week "
                            "the NFL calendar hasn't rolled past yet, re-pull later")
                fail(f"records {season} {handle(uid)}: games.json gives "
                     f"{mine[0]}-{mine[1]}-{mine[2]}, PF {mine[3]}, PA {mine[4]}; Sleeper says "
                     f"{theirs[0]}-{theirs[1]}-{theirs[2]}, PF {theirs[3]}, PA {theirs[4]}{hint}")
    return checked


def check_pairs(games):
    """Every regular week has teams/2 games; every game appears from both sides, mirrored."""
    by_week = defaultdict(list)
    for g in games:
        by_week[(g["season"], g["week"])].append(g)
    for (season, week), rows in sorted(by_week.items()):
        index = {(g["user_id"], g["opponent_id"]): g for g in rows}
        if len(index) != len(rows):
            fail(f"{season} wk{week}: a manager appears in two games")
        for g in rows:
            o = index.get((g["opponent_id"], g["user_id"]))
            if not o or o["pf"] != g["pa"] or o["pa"] != g["pf"] or o["kind"] != g["kind"] \
                    or {g["result"], o["result"]} not in ({"W", "L"}, {"T"}):
                fail(f"{season} wk{week}: {handle(g['user_id'])} v {handle(g['opponent_id'])} "
                     f"has no mirrored row")
        regular = [g for g in rows if g["kind"] == "regular"]
        if regular:
            teams = SEASONS[str(season)].get("teams") or 10
            if len(regular) != teams:
                fail(f"{season} wk{week}: {len(regular) // 2} regular-season games, "
                     f"expected {teams // 2}")
    return len(by_week)


def check_max_pf(games):
    """
    Two checks on the max_pf column. Returns (manager-seasons checked, worst row) for the
    report; failures go to FAILURES.

    1. Per manager-season, the regular-season sum of sleeper_potential() -- the same slot-order
       greedy Sleeper runs, with ELIGIBILITY applied -- must equal Sleeper's potential_points to
       the cent (after the pinned stat corrections). All 50 do. History of this check: with
       players.json positions alone, 48 of 50 agreed within 1% and two did not (2025
       paulslaats -1.42%: Travis Hunter is "DB" there, but Sleeper let him start at WR; 2024
       TnT44 +1.65%: Taysom Hill's TE/QB eligibility), which is why ELIGIBILITY exists.
    2. Every row that has a max_pf must have max_pf >= the computed score: the lineup actually
       started is one of the lineups considered. Override rows (max_pf null) are skipped.

    games.json carries best_lineup() rather than sleeper_potential(). They differ only where
    Sleeper's greedy sits below the true optimum -- 2023 week 9 and 2024 week 11, both TnT44,
    both Taysom Hill outscoring his quarterback -- and there the true figure is the right one:
    in 2024 week 11 TnT44 scored 140.88 against a Sleeper "potential" of 125.82.
    """
    total = defaultdict(float)
    for g in games:
        if g["kind"] == "regular":
            total[(str(g["season"]), g["user_id"])] += g["potential"]
        if g["max_pf"] is not None and g["max_pf"] < g["computed"] - 0.005:
            fail(f"max_pf {g['season']} wk{g['week']} {handle(g['user_id'])}: best lineup "
                 f"{g['max_pf']} is below the {g['computed']} the roster actually scored")
        if g["max_pf"] is not None and g["max_pf"] < r2(g["potential"]) - 0.005:
            fail(f"max_pf {g['season']} wk{g['week']} {handle(g['user_id'])}: best lineup "
                 f"{g['max_pf']} is below Sleeper's greedy {r2(g['potential'])}")
    rows = []
    for (season, uid), mine in sorted(total.items()):
        theirs = MANAGERS[uid]["records"][season].get("potential_points")
        pin = STAT_CORRECTIONS.get((season, uid), {}).get("pf", 0.0)
        gap = None if theirs is None else r2(mine) - theirs - pin
        rows.append((abs(gap) if gap is not None else float("inf"), gap, season, uid, r2(mine), theirs))
        if gap is None or abs(gap) > CENT:
            fail(f"max_pf {season} {handle(uid)}: lineups sum to {r2(mine)}, Sleeper's "
                 f"potential_points is {theirs}")
    rows.sort(reverse=True)
    return len(rows), rows[0]


# --------------------------------------------------------------------------------------
# Season notes
# --------------------------------------------------------------------------------------

def season_trades(season):
    """
    Completed trades with everything resolved: players to names, picks and FAAB to user_ids.

    adds/drops are already user_ids in transactions.json. draft_picks and faab_transfers are
    still raw Sleeper, keyed by roster ID in the league where the trade happened -- which is
    the trade's own season -- so they go through that season's roster map. A pick's roster_id
    is its ORIGINAL owner; owner_id is who receives it in this trade.
    """
    r2u = roster_map(season)
    out = []
    for t in TRANSACTIONS:
        if t["season"] != season or t["type"] != "trade" or t["status"] != "complete":
            continue
        sides = {uid: {"user_id": uid, "players": [], "picks": [], "faab": 0}
                 for uid in t["managers"] if uid}
        for pid, uid in (t.get("adds") or {}).items():
            sides.setdefault(uid, {"user_id": uid, "players": [], "picks": [], "faab": 0})
            sides[uid]["players"].append(player(pid))
        for pk in t.get("draft_picks") or []:
            to = r2u.get(pk.get("owner_id"))
            if to not in sides:
                fail(f"{season} trade {t['transaction_id']}: pick goes to roster "
                     f"{pk.get('owner_id')}, not a party to the trade")
                continue
            sides[to]["picks"].append({"season": str(pk["season"]), "round": pk["round"],
                                       "original_owner": r2u.get(pk.get("roster_id"))})
        for f in t.get("faab_transfers") or []:
            to = r2u.get(f.get("receiver"))
            if to in sides:
                sides[to]["faab"] += f.get("amount") or 0
        for s in sides.values():
            s["players"].sort(key=lambda p: p["name"])
            s["picks"].sort(key=lambda p: (p["season"], p["round"]))
        out.append({"week": t["week"], "date": t["date"], "id": t["transaction_id"],
                    "teams": sorted(sides.values(), key=lambda s: s["user_id"])})
    out.sort(key=lambda t: (t["date"], t["id"]))
    return out


def season_top_scorers(season):
    """
    Each team's top three players by points scored IN THE STARTING LINEUP, over every completed
    fixture week -- playoffs and consolation included, matching derive_mvps() in
    derive-narratives.py so the site and the blog name the same MVP. Bench points never won
    anybody a game.
    """
    tally = defaultdict(lambda: defaultdict(lambda: [0.0, 0]))
    for week in league_weeks(season):
        for uid, row in WEEKS[season][str(week)].items():
            if not has_matchup(row):
                continue
            for pid, pts in zip(row.get("starters") or [], row.get("starters_points") or []):
                if str(pid) == "0":     # Sleeper writes '0' into an unfilled slot
                    continue
                cell = tally[uid][str(pid)]
                cell[0] += pts
                cell[1] += 1
    out = {}
    for uid, players in sorted(tally.items()):
        best = sorted(players.items(), key=lambda kv: (-kv[1][0], kv[0]))[:3]
        out[uid] = [dict(player(pid), points=r2(pts), starts=n) for pid, (pts, n) in best]
    return out


def season_extremes(games, season, n=3):
    rows = [g for g in games if g["season"] == int(season)]
    pick = lambda g: {"week": g["week"], "user_id": g["user_id"], "opponent_id": g["opponent_id"],
                      "points": g["pf"], "kind": g["kind"]}
    high = sorted(rows, key=lambda g: (-g["pf"], g["week"], g["user_id"]))[:n]
    low = sorted(rows, key=lambda g: (g["pf"], g["week"], g["user_id"]))[:n]
    return [pick(g) for g in high], [pick(g) for g in low]


def build_notes(games):
    out = {}
    for season in sorted({str(g["season"]) for g in games}, key=int):
        high, low = season_extremes(games, season)
        out[season] = {
            "through_week": max(g["week"] for g in games if g["season"] == int(season)),
            "trades": season_trades(season),
            "top_scorers": season_top_scorers(season),
            "high_weeks": high,
            "low_weeks": low,
        }
    return out


# --------------------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------------------

def columnar(games):
    """
    Column header plus one array per column, with managers and kinds as indexes into short
    lists. ~750 rows of repeated keys would otherwise be most of the file.
    """
    managers = sorted({g["user_id"] for g in games} | {g["opponent_id"] for g in games})
    mi = {u: i for i, u in enumerate(managers)}
    cols = ["season", "week", "manager", "opponent", "pf", "pa", "result", "kind", "max_pf"]
    data = {c: [] for c in cols}
    for g in games:
        data["season"].append(g["season"])
        data["week"].append(g["week"])
        data["manager"].append(mi[g["user_id"]])
        data["opponent"].append(mi[g["opponent_id"]])
        data["pf"].append(g["pf"])
        data["pa"].append(g["pa"])
        data["result"].append(g["result"])
        data["kind"].append(KINDS.index(g["kind"]))
        data["max_pf"].append(g["max_pf"])
    last = games[-1]
    return {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "through": {"season": last["season"], "week": last["week"]},
        "nfl_state": NFL_STATE,
        "count": len(games),
        "managers": managers,
        "kinds": KINDS,
        "columns": cols,
        "data": [data[c] for c in cols],
    }


def write(name, payload):
    path = os.path.join(DATA, name)
    raw = json.dumps(payload, separators=(",", ":")).encode()
    with open(path, "wb") as f:
        f.write(raw)
    return len(raw), len(gzip.compress(raw, 9))


def main():
    games = build_games()
    if not games:
        print("no completed games found", file=sys.stderr)
        return 1

    n_records = check_records(games)
    n_weeks = check_pairs(games)
    n_max, worst = check_max_pf(games)

    seasons = sorted({g["season"] for g in games})
    by_kind = defaultdict(int)
    for g in games:
        by_kind[g["kind"]] += 1
    print(f"{len(games)} team-games, {len(games) // 2} games, {n_weeks} weeks, "
          f"seasons {seasons[0]}-{seasons[-1]}, through {games[-1]['season']} wk{games[-1]['week']}")
    print("  " + ", ".join(f"{by_kind[k]} {k}" for k in KINDS))
    print(f"check: records    {n_records} manager-seasons against league-history.json")
    print(f"check: pairs      {n_weeks} weeks, each game mirrored, five per regular week")
    n_override = sum(1 for g in games if g["max_pf"] is None)
    print(f"check: max_pf     {n_max} manager-seasons reproduce Sleeper's potential_points to the "
          f"cent (worst {worst[1]:+.2f}: {handle(worst[3])} {worst[2]}, ours {worst[4]} v "
          f"{worst[5]}); {n_override} override rows null")

    if FAILURES:
        print(f"\n{len(FAILURES)} self-check failure(s); nothing written:", file=sys.stderr)
        for f in FAILURES[:40]:
            print(f"  {f}", file=sys.stderr)
        return 1

    notes = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "seasons": build_notes(games),
    }
    if FAILURES:
        print(f"\n{len(FAILURES)} failure(s) building season notes; games.json not written either:",
              file=sys.stderr)
        for f in FAILURES[:40]:
            print(f"  {f}", file=sys.stderr)
        return 1

    print()
    for name, payload in (("games.json", columnar(games)), ("season-notes.json", notes)):
        raw, gz = write(name, payload)
        print(f"  wrote {name:<20}{raw / 1024:6.1f} KB raw {gz / 1024:6.1f} KB gzipped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
