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
    3. max_pf (best possible lineup) is kept only if every manager-season total agrees with
       Sleeper's own potential_points to within 1%. If it doesn't, the column is dropped and
       the discrepancy reported -- that is a decision about the output, not a failure.

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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "static", "data")

KINDS = ["regular", "playoff", "placement", "consolation"]
MAX_PF_TOLERANCE = 0.01

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


def optimal_points(row, slots):
    """
    Best score available from everyone on the roster that week.

    Greedy by descending points, filling slots in roster order (dedicated slots before FLEX).
    Exact here because every FLEX-eligible position also has its own dedicated slot, so no
    player can fill a slot that a higher scorer could not -- the same argument as best_lineup()
    in week-facts.py and optimal_points() in derive-narratives.py.

    Known limitation: weeks.json does not record who was on IR that week, and Sleeper lists IR
    players in `players`, so they are in the pool here although they could not be started.
    That is one reason this figure is checked against Sleeper's potential_points before it is
    allowed into games.json at all.
    """
    pool = sorted(
        ((pts, str(pid), position(pid)) for pid, pts in (row.get("players_points") or {}).items()
         if position(pid)),
        reverse=True,
    )
    used, total = set(), 0.0
    for slot in slots:
        for pts, pid, pos in pool:
            if pid in used:
                continue
            if (pos in FLEX_OK) if slot == "FLEX" else (pos == slot):
                used.add(pid)
                total += pts
                break
    return total


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
                slots = starter_slots(season)
                for (uid, row), (opp, orow) in ((pair[0], pair[1]), (pair[1], pair[0])):
                    pf, pa = official_points(row), official_points(orow)
                    games.append({
                        "season": int(season), "week": week, "user_id": uid, "opponent_id": opp,
                        "pf": pf, "pa": pa,
                        "result": "W" if pf > pa else "L" if pf < pa else "T",
                        "kind": kind,
                        "max_pf": r2(optimal_points(row, slots)),
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
    Per manager-season: sum of weekly max_pf over regular-season games against Sleeper's
    potential_points. Returns (passed, worst rows) -- worst first, by relative gap.

    Verdict on 2026-10-02: 48 of 50 manager-seasons agree within 1% (most within 0.05%, the
    residue being the pinned stat corrections above), two do not, so max_pf is left out:

      2025 paulslaats  -1.42%  Travis Hunter is "DB" in players.json, which holds only today's
                               primary position; Sleeper let him start at WR. Counting him as
                               a WR reproduces Sleeper's 1730.22 to the cent.
      2024 TnT44       +1.65%  Taysom Hill. As a TE every week we get 1830.34, as QB-only
                               1785.90; Sleeper's 1800.60 sits between, so his eligibility (or
                               IR stints) varied week to week. weeks.json records neither.

    Both are history the committed data cannot reconstruct, so this is not a tolerance problem
    and the tolerance stays at 1%.
    """
    total = defaultdict(float)
    for g in games:
        if g["kind"] == "regular":
            total[(str(g["season"]), g["user_id"])] += g["max_pf"]
    rows = []
    for (season, uid), mine in total.items():
        theirs = MANAGERS[uid]["records"][season].get("potential_points") or 0
        gap = (mine - theirs) / theirs if theirs else float("inf")
        rows.append((abs(gap), gap, season, uid, r2(mine), theirs))
    rows.sort(reverse=True)
    return all(r[0] <= MAX_PF_TOLERANCE for r in rows), rows


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

def columnar(games, with_max_pf):
    """
    Column header plus one array per column, with managers and kinds as indexes into short
    lists. ~750 rows of repeated keys would otherwise be most of the file.
    """
    managers = sorted({g["user_id"] for g in games} | {g["opponent_id"] for g in games})
    mi = {u: i for i, u in enumerate(managers)}
    cols = ["season", "week", "manager", "opponent", "pf", "pa", "result", "kind"]
    if with_max_pf:
        cols.append("max_pf")
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
        if with_max_pf:
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
    max_ok, gaps = check_max_pf(games)

    seasons = sorted({g["season"] for g in games})
    by_kind = defaultdict(int)
    for g in games:
        by_kind[g["kind"]] += 1
    print(f"{len(games)} team-games, {len(games) // 2} games, {n_weeks} weeks, "
          f"seasons {seasons[0]}-{seasons[-1]}, through {games[-1]['season']} wk{games[-1]['week']}")
    print("  " + ", ".join(f"{by_kind[k]} {k}" for k in KINDS))
    print(f"check: records    {n_records} manager-seasons against league-history.json")
    print(f"check: pairs      {n_weeks} weeks, each game mirrored, five per regular week")
    worst = gaps[0]
    print(f"check: max_pf     worst {worst[1] * 100:+.2f}% ({handle(worst[3])} {worst[2]}: "
          f"{worst[4]} v Sleeper {worst[5]}), tolerance {MAX_PF_TOLERANCE * 100:.0f}% -> "
          + ("INCLUDED" if max_ok else "LEFT OUT of games.json"))
    if not max_ok:
        over = [g for g in gaps if g[0] > MAX_PF_TOLERANCE]
        print(f"  {len(over)} of {len(gaps)} manager-seasons outside tolerance; worst five:")
        for _, gap, season, uid, mine, theirs in gaps[:5]:
            print(f"    {season} {handle(uid):16s} ours {mine:9.2f}  Sleeper {theirs:9.2f}  {gap * 100:+.2f}%")

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
    for name, payload in (("games.json", columnar(games, max_ok)), ("season-notes.json", notes)):
        raw, gz = write(name, payload)
        print(f"  wrote {name:<20}{raw / 1024:6.1f} KB raw {gz / 1024:6.1f} KB gzipped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
