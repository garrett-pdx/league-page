#!/usr/bin/env python3
"""
Turn static/data/weeks.json into facts you can actually read.

weeks.json is 366 KB of per-player weekly scores for all 72 played weeks. It answers almost
anything you ask it, but you have to know the question first -- you cannot skim it. This script
asks the interesting questions once and writes the answers out twice:

    static/data/narratives.json   structured facts, each carrying a plain-English `text`
    docs/league-lore.md           the same thing grouped and skimmable

AUTHORING AID ONLY. Nothing in src/ fetches either file, and nothing should without a deliberate
decision -- narratives.json is not size-budgeted for the browser. It exists so that writing a
recap, a manager blurb or a homepage paragraph starts from real facts instead of a fresh query.

Both `text` and the structured fields are emitted on purpose. Prose alone cannot be re-sorted or
re-toned, and would fight an LLM writing posts by making it paraphrase finished sentences instead
of composing from data. Structure alone is what we already had and could not read.

Run:  python3 scripts/derive-narratives.py
Reads only committed files. No network, no Sleeper calls.

DEFINITIONS. Every number in the output means exactly one of these:

  - Fixture: a row with a real matchup_id in a COMPLETED week (week_complete() in
    derive-site-data.py). That excludes the fictional week 18 (matchup_id 0), the teams outside
    both brackets in weeks 16-17 (matchup_id null), and any week still in progress.
  - Game score: the OFFICIAL score -- a commissioner's custom_points beats the computed points
    (official_points() in derive-site-data.py). Results, margins, highs and lows, streaks,
    head-to-head and the records check all use it. One override exists: 2024 week 8,
    tuckersdumbteam 137.74 v BBrown16 122.54 (computed 150.34 / 148.74); any fact quoting that
    game says so.
  - Player value for a manager (MVPs, keepers, draft steals and busts, FAAB "after that"): points
    the player scored IN THAT MANAGER'S STARTING LINEUP, in fixtures only, playoff and
    consolation games included. Bench points, and points scored for anybody else, never count.
    The site's season-notes top scorers use the same rule, and the self-check enforces it.
  - Optimal lineup / points left on the bench: the best legal lineup from everyone in
    players_points, against the COMPUTED score (player-level scoring stays as recorded). Same
    greedy as derive-site-data.py, plus the two position-eligibility cases Sleeper itself used
    (ELIGIBILITY below). A manager-season's bench facts are only emitted if Sleeper's own
    potential_points is reproduced to the cent; otherwise they are suppressed, never guessed.
  - The season in progress is labelled "so far, through week N" wherever a season total is
    quoted, and is left out of rankings that compare whole seasons (keepers, year-on-year swings).

Self-checks run before anything is written, and the script exits non-zero if one fails:
  1. Per-manager regular-season W/L/T, points for and points against, from THIS script's own
     pairing of fixtures, match league-history.json records (STAT_CORRECTIONS pinned exactly as
     in derive-site-data.py).
  2. The optimal-lineup function agrees with derive-site-data's optimal_points() on every
     fixture row that has no eligibility override.
  3. Every season MVP equals derive-site-data's top scorer for that manager-season.
"""

import importlib.util
import json
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "static", "data")
DOCS = os.path.join(ROOT, "docs")


def load(name):
    with open(os.path.join(DATA, name)) as f:
        return json.load(f)


def _load_site_data():
    """
    derive-site-data.py, imported as a module so the two scripts share one definition of a
    completed week, an official score, an optimal lineup and the pinned stat corrections. Its
    module level only loads the committed JSON; main() is guarded and never runs from here.
    """
    path = os.path.join(ROOT, "scripts", "derive-site-data.py")
    spec = importlib.util.spec_from_file_location("derive_site_data", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SITE = _load_site_data()

WEEKS = SITE.WEEKS
PLAYERS = SITE.PLAYERS
HISTORY = SITE.HISTORY
TRANSACTIONS = SITE.TRANSACTIONS
KEEPERS = load("keepers.json")["keepers"]

MANAGERS = HISTORY["managers"]
SEASONS = HISTORY["seasons"]
STANDINGS = HISTORY["final_standings"]

# Positions come from SITE.position(): FLEX takes RB/WR/TE, and the one fullback in the player
# set is treated as a running back.

# Positions Sleeper actually allowed, where players.json (today's primary position only) is
# wrong: Taysom Hill TE in 2022 and QB/TE from 2023, Travis Hunter WR in 2025. The table, and the
# reasoning behind each entry, live in derive-site-data.py (the lower layer, which games.json's
# max_pf is built from); with it all 50 manager-seasons reproduce Sleeper's potential_points to
# the cent, and check_optimal() re-proves that on every run.
ELIGIBILITY = SITE.ELIGIBILITY

FAILURES = []

# Printed at the top of docs/league-lore.md and stored in narratives.json, so a writer reading
# a fact knows what its number counts.
DEFINITIONS = [
    "Game scores are official: a commissioner override (custom_points) beats the computed score. "
    "The one so far is 2024 week 8, tuckersdumbteam 137.74 v BBrown16 122.54 (computed 150.34 to "
    "148.74); facts quoting it say so.",
    "A player's points for a manager (MVPs, keepers, draft steals and busts, FAAB) are points "
    "scored in that manager's starting lineup, in real fixtures, playoff and consolation games "
    "included. Bench points and points scored for anyone else never count.",
    "Week 18 and the weeks-16-17 byes of teams outside both brackets are not fixtures and count "
    "for nothing. Weekly facts from weeks 16-17 name the kind of game.",
    "Points left on the bench = the best legal lineup from the whole roster minus the computed "
    "score. Every manager-season is checked against Sleeper's potential_points before its bench "
    "facts are stated.",
    "A season in progress is labelled \"so far\" and kept out of whole-season comparisons "
    "(keepers, year-on-year swings).",
]


def handle(user_id):
    return MANAGERS.get(user_id, {}).get("handle", user_id)


def pname(pid):
    return PLAYERS.get(str(pid), {}).get("n", f"player {pid}")


def r1(x):
    return round(x + 0.0, 1)


def season_played(season):
    """
    Did this season actually happen? Structural presence is not enough.

    Once Sleeper publishes a season's schedule -- which it does before week 1 is played --
    every week comes back fully formed: ten rosters, eight starters each, real non-zero
    matchup_ids, and every single score 0.0. The 2026 season looked exactly like this on the
    day before kickoff, and `if WEEKS[s]` (merely non-empty) waved it straight through.

    The damage was not hypothetical. Every 2026 player "scored" 0.0, so 2026 swept every
    worst-of derivation, and twenty keepers tying at exactly (0.0, "2026") made
    derive_keeper_value()'s sort fall through to comparing raw dicts, which is a TypeError
    and took the whole script down.

    Same family as the week-18 trap in has_matchup(): the shape is real, the content is not.
    A season counts once it has a completed fixture week, which requires a point scored.
    """
    return season in WEEKS and bool(league_weeks(season))


def played_seasons():
    return sorted((s for s in WEEKS if season_played(s)), key=int)


def season_complete(season):
    return SEASONS.get(season, {}).get("status") == "complete"


def last_week(season):
    weeks = league_weeks(season)
    return int(weeks[-1]) if weeks else None


def has_matchup(row):
    """
    Sleeper writes matchup_id 0, not null, for a week that is not a real fixture.

    Every season here carries a week 18 in which all ten teams sit at matchup_id 0 and nobody
    sets a lineup -- median score around 55 against roughly 100 in a played week. Testing
    `matchup_id is not None` lets that week through, which is how an earlier run of this script
    invented a third playoff round and paired the champion against an arbitrary opponent.
    Treat falsy as "no fixture" everywhere -- per ROW, not per week: in weeks 16-17 the two
    teams outside both brackets sit at null while everyone else plays, and their starters
    once padded MVP totals (Josh Jacobs' 2025 for TnT44 read 218.1, of which 4.6 came from a
    week TnT44 had no game).
    """
    return SITE.has_matchup(row)


_LEAGUE_WEEKS = {}


def league_weeks(season):
    """
    Completed weeks with at least one real fixture, as strings, ascending.

    Delegates to derive-site-data, which also refuses a week the NFL calendar has not moved
    past -- the committed weeks.json should never hold one, but an old file did.
    """
    if season not in _LEAGUE_WEEKS:
        _LEAGUE_WEEKS[season] = [str(w) for w in SITE.league_weeks(season)] if season in WEEKS else []
    return _LEAGUE_WEEKS[season]


def playoff_rounds(season):
    bracket = HISTORY.get("brackets", {}).get(season, {}).get("winners", [])
    return max((row.get("r", 0) for row in bracket), default=0)


def week_rows(season):
    """
    (week, {user: row}) for completed fixture weeks, FIXTURE ROWS ONLY. Use this rather than
    iterating WEEKS directly.
    """
    for week in league_weeks(season):
        yield week, {u: r for u, r in WEEKS[season][week].items() if has_matchup(r)}


def official(row):
    """The score that counted: custom_points when a commissioner set it, else points."""
    return SITE.official_points(row)


def computed(row):
    """The score Sleeper computed from the starters -- what bench and optimal maths compare to."""
    return row.get("points") or 0.0


def overridden(*rows):
    return any(r.get("custom_points") is not None for r in rows)


def override_note(first, second):
    """Clause for a fact quoting an overridden game, scores in the same order as the fact's."""
    if not overridden(first, second):
        return ""
    return (f" (a commissioner override; Sleeper computed {computed(first):.2f} to "
            f"{computed(second):.2f})")


_KINDS = {}


def game_kind(season, week, user):
    """regular / playoff / placement / consolation for this user's fixture, from the brackets."""
    if int(week) < SEASONS[season]["playoff_week_start"]:
        return "regular"
    if season not in _KINDS:
        _KINDS[season] = SITE.bracket_kinds(season)
    row = WEEKS[season][str(week)][user]
    opp = next(u for u, r in WEEKS[season][str(week)].items()
               if u != user and has_matchup(r) and r["matchup_id"] == row["matchup_id"])
    return _KINDS[season].get((int(week), frozenset((user, opp))), "postseason")


KIND_NOTE = {"regular": "", "playoff": " (a playoff game)", "placement": " (the third-place game)",
             "consolation": " (a consolation game)", "postseason": " (a postseason game)"}


def kind_note(season, week, user):
    return KIND_NOTE[game_kind(season, week, user)]


def season_scope(season):
    """How a season total is qualified in text."""
    if season_complete(season):
        return "playoff and consolation games included"
    return f"{season} so far, through week {last_week(season)}"


def started(row):
    """(player_id, points) for real starters. Sleeper writes '0' into an unfilled slot."""
    return [
        (str(p), pt)
        for p, pt in zip(row["starters"], row["starters_points"])
        if str(p) != "0"
    ]


def benched(row):
    """Rostered players who were not started that week."""
    on_field = {p for p, _ in started(row)}
    return [
        (str(p), pt)
        for p, pt in row.get("players_points", {}).items()
        if str(p) not in on_field
    ]


# One definition of each, shared with derive-site-data.py.
eligible = SITE.eligible                    # (season, pid) -> set of positions
sleeper_potential = SITE.sleeper_potential  # (season, row): Sleeper's own slot-order greedy
optimal_points = SITE.best_lineup           # (season, row): the true best legal lineup


def matchups(season, week):
    """[(user_a, row_a, user_b, row_b)] for the given completed week, fixtures only."""
    by_id = defaultdict(list)
    for user, row in WEEKS[season][week].items():
        if has_matchup(row):
            by_id[row["matchup_id"]].append((user, row))
    for mid, pair in by_id.items():
        if len(pair) != 2:
            FAILURES.append(f"{season} wk{week} matchup {mid}: {len(pair)} teams, expected 2")
    return [(a[0], a[1], b[0], b[1]) for pair in by_id.values() if len(pair) == 2 for a, b in [pair]]


# --------------------------------------------------------------------------------------
# Starting-lineup points, the one measure of a player's value to a manager
# --------------------------------------------------------------------------------------

_STARTS = None


def starts_index():
    """(season, user, player_id) -> [(week, points)] for every start in a fixture."""
    global _STARTS
    if _STARTS is None:
        _STARTS = defaultdict(list)
        for season in played_seasons():
            for week, rows in week_rows(season):
                for user, row in rows.items():
                    for pid, pts in started(row):
                        _STARTS[(season, user, pid)].append((int(week), pts))
    return _STARTS


def starter_points(season, user, pid, from_week=None):
    """
    (points, starts): what `pid` scored in `user`'s starting lineup that season, in fixtures,
    playoff and consolation games included; from `from_week` onward if given.
    """
    rows = starts_index().get((season, user, str(pid)), [])
    picked = [pts for w, pts in rows if from_week is None or w >= int(from_week)]
    return sum(picked), len(picked)


def starts_text(n):
    return f"{n} start{'s' if n != 1 else ''}"


# --------------------------------------------------------------------------------------
# Self-checks
# --------------------------------------------------------------------------------------

VERIFIED_OPTIMAL = set()     # (season, user) whose bench and optimal facts may be stated


def check_records():
    """
    Regular-season W/L/T, PF and PA from this script's own fixtures and official scores,
    against league-history.json records, with derive-site-data's pinned stat corrections.
    """
    tally = defaultdict(lambda: [0, 0, 0, 0.0, 0.0])
    for season in played_seasons():
        start = SEASONS[season]["playoff_week_start"]
        for week in league_weeks(season):
            if int(week) >= start:
                continue
            for ua, ra, ub, rb in matchups(season, week):
                for u, mine, theirs in ((ua, official(ra), official(rb)), (ub, official(rb), official(ra))):
                    t = tally[(season, u)]
                    t[0 if mine > theirs else 1 if mine < theirs else 2] += 1
                    t[3] += mine
                    t[4] += theirs
    checked = 0
    for uid, m in MANAGERS.items():
        for season, rec in m.get("records", {}).items():
            if not season_played(season):
                continue
            w, l, t, pf, pa = tally.get((season, uid), [0, 0, 0, 0.0, 0.0])
            theirs = (rec["wins"] or 0, rec["losses"] or 0, rec["ties"] or 0)
            pin = SITE.STAT_CORRECTIONS.get((season, uid), {})
            pf_gap = SITE.r2(pf) - SITE.r2(rec["points_for"]) - pin.get("pf", 0.0)
            pa_gap = SITE.r2(pa) - SITE.r2(rec["points_against"]) - pin.get("pa", 0.0)
            checked += 1
            if (w, l, t) != theirs or abs(pf_gap) > SITE.CENT or abs(pa_gap) > SITE.CENT:
                FAILURES.append(
                    f"records {season} {handle(uid)}: narratives give {w}-{l}-{t}, PF {pf:.2f}, "
                    f"PA {pa:.2f}; league-history.json says {theirs[0]}-{theirs[1]}-{theirs[2]}, "
                    f"PF {rec['points_for']}, PA {rec['points_against']}")
    for (season, uid) in tally:
        if season not in MANAGERS.get(uid, {}).get("records", {}):
            FAILURES.append(f"records {season} {handle(uid)}: has fixtures but no Sleeper record")
    return checked


def check_optimal():
    """
    1. On every fixture row with no ELIGIBILITY entry, optimal_points() must equal
       derive-site-data's optimal_points() -- one definition, not two. A mismatch fails.
    2. Per manager-season, the regular-season sum of sleeper_potential() must reproduce
       Sleeper's potential_points to the cent (after pinned stat corrections). Those that do
       go in VERIFIED_OPTIMAL; those that don't have their bench facts suppressed, loudly.
    Returns the list of unverified (season, user, ours, sleeper).
    """
    totals = defaultdict(float)
    for season in played_seasons():
        slots = SITE.starter_slots(season)
        start = SEASONS[season]["playoff_week_start"]
        for week, rows in week_rows(season):
            for user, row in rows.items():
                if not any((season, str(p)) in ELIGIBILITY for p in row.get("players_points") or {}):
                    ours, theirs = optimal_points(season, row), SITE.optimal_points(row, slots)
                    if abs(ours - theirs) > 1e-6:
                        FAILURES.append(f"optimal {season} wk{week} {handle(user)}: {ours:.2f} here, "
                                        f"{theirs:.2f} in derive-site-data")
                if int(week) < start:
                    totals[(season, user)] += sleeper_potential(season, row)
    unverified = []
    for (season, user), ours in sorted(totals.items()):
        sleeper = MANAGERS[user]["records"][season].get("potential_points")
        pin = SITE.STAT_CORRECTIONS.get((season, user), {}).get("pf", 0.0)
        if sleeper is not None and abs(SITE.r2(ours) - sleeper - pin) <= SITE.CENT:
            VERIFIED_OPTIMAL.add((season, user))
        else:
            unverified.append((season, user, SITE.r2(ours), sleeper))
    return unverified


def check_mvps_match_site():
    """Each manager-season's top starter here must be the site's top scorer, to the cent."""
    for season in played_seasons():
        site = SITE.season_top_scorers(season)
        for user, best in site.items():
            tally = {pid: starter_points(season, user, pid)[0]
                     for (s, u, pid) in starts_index() if s == season and u == user}
            mine = max(tally.values(), default=0.0)
            if abs(SITE.r2(mine) - best[0]["points"]) > 0.005:
                FAILURES.append(f"mvp {season} {handle(user)}: {mine:.2f} here, "
                                f"{best[0]['points']} on the site")


FACTS = []


def fact(category, text, season=None, week=None, managers=None, players=None, **values):
    FACTS.append(
        {
            "category": category,
            "season": season,
            "week": int(week) if week is not None else None,
            "managers": managers or [],
            "players": [str(p) for p in (players or [])],
            "values": {k: (r1(v) if isinstance(v, float) else v) for k, v in values.items()},
            "text": text,
        }
    )


# --------------------------------------------------------------------------------------
# Players
# --------------------------------------------------------------------------------------

def derive_mvps():
    """
    Points a player scored IN THIS MANAGER'S STARTING LINEUP, fixtures only, playoffs and
    consolation included. Bench points never won anybody a game. Ties go to the player id, so
    the output is deterministic.
    """
    per_season = defaultdict(lambda: defaultdict(lambda: [0.0, 0]))
    career = defaultdict(lambda: defaultdict(lambda: [0.0, 0]))
    league_season = defaultdict(lambda: defaultdict(float))

    for (season, user, pid), rows in starts_index().items():
        pts, n = sum(p for _, p in rows), len(rows)
        for cell in (per_season[(season, user)][pid], career[user][pid]):
            cell[0] += pts
            cell[1] += n
        league_season[season][pid] += pts

    def top(tally):
        return min(tally.items(), key=lambda kv: (-kv[1][0], kv[0]))

    for (season, user), tally in per_season.items():
        pid, (pts, n) = top(tally)
        fact(
            "season_mvp",
            f"{pname(pid)} was {handle(user)}'s {season} MVP: {r1(pts)} points in his starting "
            f"lineup ({starts_text(n)}; {season_scope(season)}).",
            season=season, managers=[user], players=[pid], points=pts, starts=n,
        )

    seasons = played_seasons()
    span = f"{seasons[0]}-{seasons[-1]}, {seasons[-1]} through week {last_week(seasons[-1])}" \
        if not season_complete(seasons[-1]) else f"{seasons[0]}-{seasons[-1]}"
    for user, tally in career.items():
        pid, (pts, n) = top(tally)
        fact(
            "career_mvp",
            f"No player has scored more in {handle(user)}'s starting lineup than {pname(pid)}: "
            f"{r1(pts)} points in {starts_text(n)} ({span}, postseason included).",
            managers=[user], players=[pid], points=pts, starts=n,
        )

    for season, tally in league_season.items():
        ranked = sorted(tally.items(), key=lambda kv: (-kv[1], kv[0]))[:3]
        for rank, (pid, pts) in enumerate(ranked, 1):
            fact(
                "league_season_leader",
                f"{pname(pid)} was the {rank}{'st' if rank == 1 else 'nd' if rank == 2 else 'rd'} "
                f"highest-scoring player in the league's starting lineups in {season}, with "
                f"{r1(pts)} ({season_scope(season)}).",
                season=season, players=[pid], points=pts, rank=rank,
            )


def derive_big_weeks():
    rows = []
    for season in played_seasons():
        for week, wk in week_rows(season):
            for user, row in wk.items():
                for pid, pts in started(row):
                    rows.append((pts, season, week, user, pid))
    for pts, season, week, user, pid in sorted(rows, reverse=True)[:15]:
        fact(
            "top_week_performance",
            f"{pname(pid)} put up {r1(pts)} for {handle(user)} in week {week} of {season}"
            f"{kind_note(season, week, user)} -- one of the biggest single weeks anyone has started.",
            season=season, week=week, managers=[user], players=[pid], points=pts,
        )


# --------------------------------------------------------------------------------------
# Lineup decisions
# --------------------------------------------------------------------------------------

def derive_benchings():
    rows = []
    for season in played_seasons():
        for week, wk in week_rows(season):
            for user, row in wk.items():
                for pid, pts in benched(row):
                    rows.append((pts, season, week, user, pid))
    for pts, season, week, user, pid in sorted(rows, reverse=True)[:15]:
        fact(
            "worst_benching",
            f"{handle(user)} left {pname(pid)} on the bench in week {week} of {season}"
            f"{kind_note(season, week, user)}. He scored {r1(pts)}.",
            season=season, week=week, managers=[user], players=[pid], points=pts,
        )


def derive_whatifs():
    """
    Points left on the bench = optimal_points() minus the COMPUTED score, fixtures only, and
    only for manager-seasons in VERIFIED_OPTIMAL. Two decimals: a perfect lineup is a gap
    below a cent.
    """
    gaps, perfect, weeks = [], defaultdict(int), defaultdict(int)
    for season in played_seasons():
        for week, wk in week_rows(season):
            for user, row in wk.items():
                if (season, user) not in VERIFIED_OPTIMAL:
                    continue
                best = optimal_points(season, row)
                gap = best - computed(row)
                weeks[user] += 1
                if gap < -0.005:
                    FAILURES.append(f"optimal {season} wk{week} {handle(user)}: {best:.2f} is below "
                                    f"the {computed(row):.2f} actually scored")
                if gap <= 0.005:
                    perfect[user] += 1
                else:
                    gaps.append((round(gap, 2), season, week, user, computed(row), best))

    for gap, season, week, user, actual, best in sorted(gaps, key=lambda g: (-g[0], g[1], int(g[2])))[:12]:
        opp_row = next(r for u, r in WEEKS[season][week].items()
                       if u != user and r.get("matchup_id") == WEEKS[season][week][user]["matchup_id"])
        note = override_note(WEEKS[season][week][user], opp_row)
        fact(
            "biggest_whatif",
            f"In week {week} of {season}{kind_note(season, week, user)}, {handle(user)} scored "
            f"{actual:.2f}{note} from a roster whose best lineup would have scored {best:.2f} -- "
            f"{gap:.2f} points left on the bench.",
            season=season, week=week, managers=[user], actual=round(actual, 2),
            optimal=round(best, 2), gap=gap,
        )

    for user, count in sorted(perfect.items(), key=lambda kv: (-kv[1], handle(kv[0]))):
        fact(
            "perfect_lineups",
            f"{handle(user)} has started the optimal lineup {count} time{'s' if count != 1 else ''} "
            f"in {weeks[user]} games (postseason included).",
            managers=[user], count=count, games=weeks[user],
        )


def derive_bench_beats_starters():
    """Whole bench against the starters' COMPUTED score -- a roster fact, not an eligibility one."""
    rows = []
    for season in played_seasons():
        for week, wk in week_rows(season):
            for user, row in wk.items():
                bench_total = sum(p for _, p in benched(row))
                if bench_total > computed(row):
                    rows.append((bench_total - computed(row), season, week, user, computed(row), bench_total))
    for margin, season, week, user, starters_pts, bench_pts in sorted(rows, reverse=True)[:8]:
        fact(
            "bench_outscored_starters",
            f"{handle(user)}'s bench outscored his starters in week {week} of {season}"
            f"{kind_note(season, week, user)}, {r1(bench_pts)} to {r1(starters_pts)}.",
            season=season, week=week, managers=[user], bench=bench_pts, starters=starters_pts, margin=margin,
        )


def derive_zeroes():
    tally = defaultdict(int)
    for season in played_seasons():
        for week, wk in week_rows(season):
            for user, row in wk.items():
                for pid, pts in started(row):
                    if pts == 0:
                        tally[user] += 1
    for user, count in sorted(tally.items(), key=lambda kv: -kv[1])[:5]:
        fact(
            "zero_starts",
            f"{handle(user)} has started a player who scored exactly nothing {count} times.",
            managers=[user], count=count,
        )


# --------------------------------------------------------------------------------------
# Matchups
# --------------------------------------------------------------------------------------

def derive_matchup_drama():
    """Official scores throughout, so a commissioner override decides the game as it did."""
    close, blowout, unlucky, lucky, shootout = [], [], [], [], []
    for season in played_seasons():
        for week in league_weeks(season):
            for ua, ra, ub, rb in matchups(season, week):
                pa_, pb_ = official(ra), official(rb)
                margin = round(abs(pa_ - pb_), 2)
                (win, wrow), (lose, lrow) = ((ua, ra), (ub, rb)) if pa_ > pb_ else ((ub, rb), (ua, ra))
                wp, lp = max(pa_, pb_), min(pa_, pb_)
                note = override_note(wrow, lrow)
                kind = kind_note(season, week, ua)
                if margin > 0:
                    close.append((margin, season, week, win, lose, wp, lp, note, kind))
                    blowout.append((margin, season, week, win, lose, wp, lp, note, kind))
                    unlucky.append((lp, season, week, lose, win, lp, wp, override_note(lrow, wrow), kind))
                    lucky.append((-wp, season, week, win, lose, wp, lp, note, kind))
                shootout.append((round(pa_ + pb_, 2), season, week, ua, ub, pa_, pb_, override_note(ra, rb), kind))

    for margin, season, week, win, lose, wp, lp, note, kind in sorted(close, key=lambda r: r[:3])[:8]:
        # Two decimals here specifically: the tightest games are decided by hundredths, and
        # rounding to one made a genuine 0.04 point win read as "by 0.0", i.e. as a tie.
        fact(
            "closest_game",
            f"{handle(win)} beat {handle(lose)} by {margin:.2f} in week {week} of {season}{kind}, "
            f"{wp:.2f} to {lp:.2f}{note}.",
            season=season, week=week, managers=[win, lose], margin=margin, winner_points=wp, loser_points=lp,
        )

    for margin, season, week, win, lose, wp, lp, note, kind in sorted(blowout, key=lambda r: (-r[0],) + r[1:3])[:8]:
        fact(
            "biggest_blowout",
            f"{handle(win)} buried {handle(lose)} by {r1(margin)} in week {week} of {season}{kind}, "
            f"{r1(wp)} to {r1(lp)}{note}.",
            season=season, week=week, managers=[win, lose], margin=margin, winner_points=wp, loser_points=lp,
        )

    for lp, season, week, lose, win, _, wp, note, kind in sorted(unlucky, key=lambda r: (-r[0],) + r[1:3])[:6]:
        fact(
            "unluckiest_loss",
            f"{handle(lose)} scored {r1(lp)} in week {week} of {season}{kind} and still lost, because "
            f"{handle(win)} went for {r1(wp)}{note}.",
            season=season, week=week, managers=[lose, win], points=lp, opponent_points=wp,
        )

    for negwp, season, week, win, lose, wp, lp, note, kind in sorted(lucky, key=lambda r: (-r[0],) + r[1:3])[:6]:
        fact(
            "luckiest_win",
            f"{handle(win)} won week {week} of {season}{kind} with just {r1(wp)} -- {handle(lose)} "
            f"managed only {r1(lp)}{note}.",
            season=season, week=week, managers=[win, lose], points=wp, opponent_points=lp,
        )

    for total, season, week, ua, ub, pa, pb, note, kind in sorted(shootout, key=lambda r: (-r[0],) + r[1:3])[:5]:
        fact(
            "highest_scoring_matchup",
            f"{handle(ua)} and {handle(ub)} combined for {r1(total)} in week {week} of {season}, "
            f"{r1(pa)} to {r1(pb)}{kind}{note}.",
            season=season, week=week, managers=[ua, ub], total=total,
        )


# --------------------------------------------------------------------------------------
# Seasons
# --------------------------------------------------------------------------------------

def derive_titles():
    for season in sorted(STANDINGS, reverse=True):
        champ = next((r["user_id"] for r in STANDINGS[season] if r["place"] == 1), None)
        if not champ:
            continue
        # Bound the run by the bracket, not by "every week from playoff_week_start onward".
        # Four teams over two rounds means weeks 16 and 17; week 18 exists in the data with no
        # fixture at all, and including it previously invented a third round.
        start = SEASONS[season]["playoff_week_start"]
        last = start + max(playoff_rounds(season), 1) - 1

        legs = []
        carried = defaultdict(float)
        for week in league_weeks(season):
            if not (start <= int(week) <= last):
                continue
            row = WEEKS[season][week].get(champ)
            if not row or not has_matchup(row):
                continue
            opp = next((u for u, r in WEEKS[season][week].items()
                        if has_matchup(r) and r["matchup_id"] == row["matchup_id"] and u != champ), None)
            if opp is None:
                continue
            legs.append((week, official(row), handle(opp), official(WEEKS[season][week][opp])))
            for pid, pts in started(row):
                carried[pid] += pts

        if not legs:
            continue
        best = sorted(carried.items(), key=lambda kv: -kv[1])[:3]
        leg_text = "; ".join(f"week {w} {r1(p)}-{r1(op)} over {o}" for w, p, o, op in legs)
        carry_text = ", ".join(f"{pname(p)} {r1(v)}" for p, v in best)
        fact(
            "championship_run",
            f"{handle(champ)} won {season}: {leg_text}. Carried through the bracket by {carry_text}.",
            season=season, managers=[champ], players=[p for p, _ in best],
            legs=[{"week": int(w), "for": r1(p), "against": r1(op)} for w, p, o, op in legs],
        )


def derive_streaks():
    for user in MANAGERS:
        seq = []
        for season in played_seasons():
            for week in league_weeks(season):
                for ua, ra, ub, rb in matchups(season, week):
                    if user in (ua, ub):
                        mine = official(ra if ua == user else rb)
                        theirs = official(rb if ua == user else ra)
                        if mine != theirs:
                            seq.append((season, week, mine > theirs))
        if not seq:
            continue
        best_w = best_l = cur = 0
        cur_win = None
        span = {}
        run_start = None
        for season, week, won in seq:
            if won == cur_win:
                cur += 1
            else:
                cur, cur_win, run_start = 1, won, (season, week)
            if won and cur > best_w:
                best_w, span["win"] = cur, (run_start, (season, week))
            if not won and cur > best_l:
                best_l, span["loss"] = cur, (run_start, (season, week))
        if best_w > 1:
            (s0, w0), (s1, w1) = span["win"]
            fact(
                "longest_win_streak",
                f"{handle(user)}'s longest winning run is {best_w} games, {s0} week {w0} through {s1} week {w1}.",
                managers=[user], length=best_w,
            )
        if best_l > 1:
            (s0, w0), (s1, w1) = span["loss"]
            fact(
                "longest_losing_streak",
                f"{handle(user)}'s longest losing run is {best_l} games, {s0} week {w0} through {s1} week {w1}.",
                managers=[user], length=best_l,
            )


def derive_head_to_head():
    """Every fixture between the pair, playoffs and consolation included, official scores."""
    tally = defaultdict(lambda: [0, 0, 0.0, 0.0, 0, []])
    for season in played_seasons():
        for week in league_weeks(season):
            for ua, ra, ub, rb in matchups(season, week):
                key = tuple(sorted((ua, ub)))
                first = key[0]
                a, b = (ra, rb) if ua == first else (rb, ra)
                pa_, pb_ = official(a), official(b)
                rec = tally[key]
                rec[2] += pa_
                rec[3] += pb_
                if pa_ > pb_:
                    rec[0] += 1
                elif pb_ > pa_:
                    rec[1] += 1
                else:
                    rec[4] += 1
                if overridden(a, b):
                    rec[5].append(f"{season} week {week}")
    for (ua, ub), (wa, wb, pa, pb, ties, over) in sorted(tally.items(), key=lambda kv: -(kv[1][0] + kv[1][1] + kv[1][4])):
        met = wa + wb + ties
        if met == 0:
            continue
        lead = handle(ua) if wa >= wb else handle(ub)
        record = f"{wa}-{wb}" + (f"-{ties}" if ties else "")
        note = (f" ({', '.join(over)} counted at the commissioner's override score)" if over else "")
        fact(
            "head_to_head",
            f"{handle(ua)} and {handle(ub)} have met {met} time{'s' if met != 1 else ''}: {record} to "
            f"{lead}, {r1(pa)} against {r1(pb)} all told{note}.",
            managers=[ua, ub], wins_first=wa, wins_second=wb, ties=ties, points_first=pa, points_second=pb,
        )


def derive_season_swings():
    """Completed seasons only: a season in progress is not a win total."""
    for user, m in MANAGERS.items():
        recs = {s: r for s, r in m.get("records", {}).items()
                if r["wins"] + r["losses"] + r["ties"] > 0 and season_complete(s)}
        years = sorted(recs, key=int)
        for prev, cur in zip(years, years[1:]):
            swing = recs[cur]["wins"] - recs[prev]["wins"]
            if abs(swing) >= 5:
                direction = "climbed" if swing > 0 else "fell"
                fact(
                    "season_swing",
                    f"{handle(user)} {direction} from {recs[prev]['wins']} wins in {prev} to "
                    f"{recs[cur]['wins']} in {cur}.",
                    season=cur, managers=[user], swing=swing,
                )


# --------------------------------------------------------------------------------------
# Draft, keepers, money
# --------------------------------------------------------------------------------------

def derive_draft_value():
    """
    A pick's value is what he scored in the DRAFTER's starting lineup that season. A steal
    traded away in October is worth what it was worth to the man who drafted him, and a bust's
    points for his next team never consoled anyone.
    """
    for season in played_seasons():
        drafts = [d for d in HISTORY["drafts"].get(season, []) if d.get("primary")]
        if not drafts:
            continue
        # Keepers occupy a draft slot but were never a draft decision, so they are not steals or
        # busts -- they are keeper decisions, and best_keeper/worst_keeper already tell that
        # story. Without this filter mikestreinz's 2024 "round 1 pick" on Christian McCaffrey
        # appeared as a draft bust and again, correctly, as a failed keeper.
        picks = [p for p in drafts[0]["picks"] if not p.get("is_keeper")]
        scored = [(starter_points(season, p.get("picked_by"), p["player_id"]), p)
                  for p in picks if p.get("player_id")]
        scope = season_scope(season)

        late = [(v, p) for v, p in scored if p["round"] >= 8]
        if late:
            (v, n), p = min(late, key=lambda x: (-x[0][0], x[1].get("pick_no") or 0))
            fact(
                "draft_steal",
                f"{pname(p['player_id'])} went in round {p['round']} of the {season} draft to "
                f"{handle(p.get('picked_by'))} and scored {r1(v)} in his starting lineup that "
                f"season ({starts_text(n)}; {scope}).",
                season=season, managers=[p.get("picked_by")], players=[p["player_id"]],
                round=p["round"], points=v, starts=n,
            )

        early = [(v, p) for v, p in scored if p["round"] <= 3]
        if early:
            (v, n), p = min(early, key=lambda x: (x[0][0], x[1].get("pick_no") or 0))
            fact(
                "draft_bust",
                f"{handle(p.get('picked_by'))} spent a round {p['round']} pick on "
                f"{pname(p['player_id'])} in {season} and got {r1(v)} points from him in the "
                f"starting lineup ({starts_text(n)}; {scope}).",
                season=season, managers=[p.get("picked_by")], players=[p["player_id"]],
                round=p["round"], points=v, starts=n,
            )


def derive_keeper_value():
    """
    A keeper's value is what he scored in the KEEPER's starting lineup that season. Completed
    seasons only: three weeks of 2026 ranked against full seasons filled every "worst keeper"
    slot with this year's keepers.
    """
    rows = []
    for season, entries in KEEPERS.items():
        if not season_played(season) or not season_complete(season):
            continue
        for k in entries:
            pts, n = starter_points(season, k["user_id"], k["player_id"])
            rows.append((pts, season, n, k))
    # Sort on the scalars only. A bare sorted() compares the last element when everything else
    # ties, and that element is a dict -- unorderable, and a crash rather than a wrong answer.
    # Ties are normal here (any two keepers who scored the same).
    tiebreak = lambda r: (r[1], r[3].get("pick_no") or 0)
    for v, season, n, k in sorted(rows, key=lambda r: (-r[0],) + tiebreak(r))[:6]:
        fact(
            "best_keeper",
            f"{handle(k['user_id'])} kept {pname(k['player_id'])} at a round {k['cost_round']} cost "
            f"in {season}; he scored {r1(v)} in {handle(k['user_id'])}'s starting lineup that "
            f"season ({starts_text(n)}, postseason included).",
            season=season, managers=[k["user_id"]], players=[k["player_id"]],
            cost_round=k["cost_round"], points=v, starts=n,
        )
    for v, season, n, k in sorted(rows, key=lambda r: (r[0],) + tiebreak(r))[:5]:
        fact(
            "worst_keeper",
            f"{handle(k['user_id'])} kept {pname(k['player_id'])} at a round {k['cost_round']} cost "
            f"in {season} and got {r1(v)} points out of him in the starting lineup "
            f"({starts_text(n)}, postseason included).",
            season=season, managers=[k["user_id"]], players=[k["player_id"]],
            cost_round=k["cost_round"], points=v, starts=n,
        )


def points_after(season, week, user, pid):
    """
    (points, starts): what a player scored IN THIS MANAGER'S STARTING LINEUP from the pickup
    week onward, fixtures only.

    Season totals are the wrong measure of a waiver bid: paulslaats paid $75 for Trevor
    Lawrence in week 16 of 2022, and quoting the full-season figure credits him with points
    scored for somebody else in weeks 1 to 15. Rostered points are wrong too: a backup who
    never starts has won nobody anything.
    """
    if not season_played(season) or week is None:
        return 0.0, 0
    return starter_points(season, user, pid, from_week=week)


def derive_money():
    spends = []
    for t in TRANSACTIONS:
        if t.get("status") != "complete" or not t.get("faab"):
            continue
        adds = t.get("adds") or {}
        for pid, user in adds.items():
            spends.append((t["faab"], t["season"], t.get("week"), user, pid))
    for amount, season, week, user, pid in sorted(spends, reverse=True)[:8]:
        pts, n = points_after(season, week, user, pid)
        scope = "postseason included" if season_complete(season) else season_scope(season)
        fact(
            "faab_splurge",
            f"{handle(user)} spent ${amount} of FAAB on {pname(pid)} in week {week} of {season}. "
            f"He scored {r1(pts)} in his starting lineup from then on ({starts_text(n)}; {scope}).",
            season=season, week=week, managers=[user], players=[pid], faab=amount, points=pts, starts=n,
        )

    trades = defaultdict(int)
    for t in TRANSACTIONS:
        if t.get("type") == "trade" and t.get("status") == "complete":
            for u in t.get("managers", []):
                trades[u] += 1
    for user, count in sorted(trades.items(), key=lambda kv: -kv[1])[:5]:
        fact(
            "trade_activity",
            f"{handle(user)} has been part of {count} completed trades.",
            managers=[user], count=count,
        )


# --------------------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------------------

CATEGORY_TITLES = [
    ("championship_run", "Championships"),
    ("season_mvp", "Season MVPs"),
    ("career_mvp", "Career MVPs"),
    ("league_season_leader", "League scoring leaders"),
    ("top_week_performance", "Biggest single weeks"),
    ("worst_benching", "Left on the bench"),
    ("biggest_whatif", "Points left behind"),
    ("bench_outscored_starters", "Bench beat the starters"),
    ("perfect_lineups", "Perfect lineups"),
    ("zero_starts", "Started a zero"),
    ("closest_game", "Closest games"),
    ("biggest_blowout", "Biggest blowouts"),
    ("unluckiest_loss", "Unluckiest losses"),
    ("luckiest_win", "Luckiest wins"),
    ("highest_scoring_matchup", "Shootouts"),
    ("longest_win_streak", "Longest winning runs"),
    ("longest_losing_streak", "Longest losing runs"),
    ("season_swing", "Big year-on-year swings"),
    ("head_to_head", "Head to head"),
    ("draft_steal", "Draft steals"),
    ("draft_bust", "Draft busts"),
    ("best_keeper", "Keepers that paid off"),
    ("worst_keeper", "Keepers that did not"),
    ("faab_splurge", "Biggest FAAB bids"),
    ("trade_activity", "Trade activity"),
]


def write_outputs():
    by_cat = defaultdict(list)
    for f in FACTS:
        by_cat[f["category"]].append(f)

    payload = {
        "generated": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
        "note": (
            "Derived from weeks.json by scripts/derive-narratives.py. Authoring aid, not fetched "
            "at runtime. Regenerate after a season with: python3 scripts/derive-narratives.py"
        ),
        "definitions": DEFINITIONS,
        "seasons": played_seasons(),
        "count": len(FACTS),
        "facts": FACTS,
    }
    out_json = os.path.join(DATA, "narratives.json")
    with open(out_json, "w") as f:
        json.dump(payload, f, indent=1)

    os.makedirs(DOCS, exist_ok=True)
    lines = [
        "# League lore",
        "",
        "Generated by `scripts/derive-narratives.py` from `static/data/weeks.json`.",
        "**Do not hand-edit** -- rerun the script instead. Nothing in `src/` reads this;",
        "it exists so writing a recap or a bio starts from facts rather than a fresh query.",
        "",
        f"{len(FACTS)} facts across seasons {', '.join(played_seasons())}"
        + (f" ({played_seasons()[-1]} through week {last_week(played_seasons()[-1])})."
           if not season_complete(played_seasons()[-1]) else "."),
        "",
        "**What the numbers mean.**",
        "",
    ] + [f"- {d}" for d in DEFINITIONS] + [""]
    for cat, title in CATEGORY_TITLES:
        items = by_cat.get(cat)
        if not items:
            continue
        lines += [f"## {title}", ""]
        for f in items:
            lines.append(f"- {f['text']}")
        lines.append("")

    out_md = os.path.join(DOCS, "league-lore.md")
    with open(out_md, "w") as f:
        f.write("\n".join(lines))

    return out_json, out_md


def main():
    n_records = check_records()
    unverified = check_optimal()
    check_mvps_match_site()
    if FAILURES:
        print(f"{len(FAILURES)} self-check failure(s); nothing written:", file=sys.stderr)
        for f in FAILURES[:40]:
            print(f"  {f}", file=sys.stderr)
        return 1
    print(f"check: records   {n_records} manager-seasons match league-history.json")
    print(f"check: optimal   {len(VERIFIED_OPTIMAL)} manager-seasons reproduce Sleeper's "
          f"potential_points to the cent; one definition with derive-site-data")
    for season, user, ours, sleeper in unverified:
        print(f"  WARNING: {season} {handle(user)} does not ({ours} v Sleeper {sleeper}); "
              f"its bench and optimal-lineup facts are suppressed")
    print("check: mvps      every season MVP matches the site's top scorer")
    print()

    derive_mvps()
    derive_big_weeks()
    derive_benchings()
    derive_whatifs()
    derive_bench_beats_starters()
    derive_zeroes()
    derive_matchup_drama()
    derive_titles()
    derive_streaks()
    derive_head_to_head()
    derive_season_swings()
    derive_draft_value()
    derive_keeper_value()
    derive_money()

    js, md = write_outputs()
    by_cat = defaultdict(int)
    for f in FACTS:
        by_cat[f["category"]] += 1
    print(f"{len(FACTS)} facts in {len(by_cat)} categories")
    for cat, title in CATEGORY_TITLES:
        if by_cat.get(cat):
            print(f"  {by_cat[cat]:>4}  {title}")
    print(f"\nwrote {os.path.relpath(js, ROOT)}")
    print(f"wrote {os.path.relpath(md, ROOT)}  ({os.path.getsize(md) // 1024} KB)")
    if FAILURES:
        # Raised while deriving (an optimal lineup below the actual score). The files are
        # already written, so fail the run loudly rather than let them be committed quietly.
        print(f"\n{len(FAILURES)} failure(s) while deriving:", file=sys.stderr)
        for f in FAILURES[:40]:
            print(f"  {f}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
