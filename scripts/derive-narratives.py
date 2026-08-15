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
"""

import json
import os
from collections import defaultdict
from itertools import combinations

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "static", "data")
DOCS = os.path.join(ROOT, "docs")


def load(name):
    with open(os.path.join(DATA, name)) as f:
        return json.load(f)


WEEKS = load("weeks.json")["weeks"]
PLAYERS = load("players.json")
HISTORY = load("league-history.json")
TRANSACTIONS = load("transactions.json")["transactions"]
KEEPERS = load("keepers.json")["keepers"]

MANAGERS = HISTORY["managers"]
SEASONS = HISTORY["seasons"]
STANDINGS = HISTORY["final_standings"]

# FLEX takes RB/WR/TE. One fullback exists in the player set; treat him as a running back.
FLEX_POSITIONS = {"RB", "WR", "TE", "FB"}
POS_ALIAS = {"FB": "RB"}


def handle(user_id):
    return MANAGERS.get(user_id, {}).get("handle", user_id)


def pname(pid):
    return PLAYERS.get(str(pid), {}).get("n", f"player {pid}")


def ppos(pid):
    raw = PLAYERS.get(str(pid), {}).get("p", "?")
    return POS_ALIAS.get(raw, raw)


def r1(x):
    return round(x + 0.0, 1)


def played_seasons():
    return sorted(s for s in WEEKS if WEEKS[s])


def has_matchup(row):
    """
    Sleeper writes matchup_id 0, not null, for a week that is not a real fixture.

    Every season here carries a week 18 in which all ten teams sit at matchup_id 0 and nobody
    sets a lineup -- median score around 55 against roughly 100 in a played week. Testing
    `matchup_id is not None` lets that week through, which is how an earlier run of this script
    invented a third playoff round and paired the champion against an arbitrary opponent.
    Treat falsy as "no fixture" everywhere.
    """
    return bool(row.get("matchup_id"))


def league_weeks(season):
    """
    Weeks that actually happened: at least one real fixture.

    Reads WEEKS directly and must keep doing so -- week_rows() is built on top of this, so
    routing it through week_rows() makes the two mutually recursive.
    """
    return sorted(
        (w for w, rows in WEEKS[season].items() if any(has_matchup(r) for r in rows.values())),
        key=int,
    )


def playoff_rounds(season):
    bracket = HISTORY.get("brackets", {}).get(season, {}).get("winners", [])
    return max((row.get("r", 0) for row in bracket), default=0)


def week_rows(season):
    """(week, rows) for real fixture weeks only. Use this rather than iterating WEEKS directly."""
    for week in league_weeks(season):
        yield week, WEEKS[season][week]


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


def optimal_points(row):
    """
    Best score available from the players on the roster that week, under
    QB / RB / RB / WR / WR / TE / FLEX / FLEX.

    Greedy is exact here because the flex pool is the leftovers of the three flex-eligible
    positions: fill each fixed slot with its own best, then take the two highest remaining
    flex-eligible players. No fixed slot competes with another for the same player.
    """
    pool = defaultdict(list)
    for pid, pts in row.get("players_points", {}).items():
        pool[ppos(pid)].append(pts)
    for pos in pool:
        pool[pos].sort(reverse=True)

    total = 0.0
    leftovers = []
    for pos, count in (("QB", 1), ("RB", 2), ("WR", 2), ("TE", 1)):
        taken = pool.get(pos, [])[:count]
        total += sum(taken)
        leftovers += pool.get(pos, [])[count:]

    leftovers.sort(reverse=True)
    total += sum(leftovers[:2])
    return total


def matchups(season, week):
    """[(user_a, row_a, user_b, row_b)] for the given week."""
    by_id = defaultdict(list)
    for user, row in WEEKS[season][week].items():
        if has_matchup(row):
            by_id[row["matchup_id"]].append((user, row))
    return [(a[0], a[1], b[0], b[1]) for pair in by_id.values() if len(pair) == 2 for a, b in [pair]]


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
    """Points a player scored WHILE STARTED. Bench points never won anybody a game."""
    per_season = defaultdict(lambda: defaultdict(float))
    career = defaultdict(lambda: defaultdict(float))
    league_season = defaultdict(lambda: defaultdict(float))

    for season in played_seasons():
        for week, rows in week_rows(season):
            for user, row in rows.items():
                for pid, pts in started(row):
                    per_season[(season, user)][pid] += pts
                    career[user][pid] += pts
                    league_season[season][pid] += pts

    for (season, user), tally in per_season.items():
        pid = max(tally, key=tally.get)
        fact(
            "season_mvp",
            f"{pname(pid)} was {handle(user)}'s {season} MVP, worth {r1(tally[pid])} points in the starting lineup.",
            season=season, managers=[user], players=[pid], points=tally[pid],
        )

    for user, tally in career.items():
        pid = max(tally, key=tally.get)
        fact(
            "career_mvp",
            f"Across every season, no player has scored more for {handle(user)} than {pname(pid)}: {r1(tally[pid])} points.",
            managers=[user], players=[pid], points=tally[pid],
        )

    for season, tally in league_season.items():
        ranked = sorted(tally.items(), key=lambda kv: -kv[1])[:3]
        for rank, (pid, pts) in enumerate(ranked, 1):
            fact(
                "league_season_leader",
                f"{pname(pid)} was the {rank}{'st' if rank == 1 else 'nd' if rank == 2 else 'rd'} "
                f"highest-scoring started player in the league in {season}, with {r1(pts)}.",
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
            f"{pname(pid)} put up {r1(pts)} for {handle(user)} in week {week} of {season} "
            f"-- one of the biggest single weeks anyone has started.",
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
            f"{handle(user)} left {pname(pid)} on the bench in week {week} of {season}. He scored {r1(pts)}.",
            season=season, week=week, managers=[user], players=[pid], points=pts,
        )


def derive_whatifs():
    gaps, perfect = [], defaultdict(int)
    for season in played_seasons():
        for week, wk in week_rows(season):
            for user, row in wk.items():
                best = optimal_points(row)
                gap = best - row["points"]
                if gap <= 0.01:
                    perfect[user] += 1
                else:
                    gaps.append((gap, season, week, user, row["points"], best))

    for gap, season, week, user, actual, best in sorted(gaps, reverse=True)[:12]:
        fact(
            "biggest_whatif",
            f"In week {week} of {season}, {handle(user)} scored {r1(actual)} with a lineup that "
            f"could have scored {r1(best)} -- {r1(gap)} points left in the bench.",
            season=season, week=week, managers=[user], actual=actual, optimal=best, gap=gap,
        )

    for user, count in sorted(perfect.items(), key=lambda kv: -kv[1]):
        if count:
            fact(
                "perfect_lineups",
                f"{handle(user)} has started the optimal lineup {count} time{'s' if count != 1 else ''}.",
                managers=[user], count=count,
            )


def derive_bench_beats_starters():
    rows = []
    for season in played_seasons():
        for week, wk in week_rows(season):
            for user, row in wk.items():
                bench_total = sum(p for _, p in benched(row))
                if bench_total > row["points"]:
                    rows.append((bench_total - row["points"], season, week, user, row["points"], bench_total))
    for margin, season, week, user, starters_pts, bench_pts in sorted(rows, reverse=True)[:8]:
        fact(
            "bench_outscored_starters",
            f"{handle(user)}'s bench outscored his starters in week {week} of {season}, "
            f"{r1(bench_pts)} to {r1(starters_pts)}.",
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
    close, blowout, unlucky, lucky, shootout = [], [], [], [], []
    for season in played_seasons():
        for week in league_weeks(season):
            for ua, ra, ub, rb in matchups(season, week):
                margin = abs(ra["points"] - rb["points"])
                win, lose = (ua, ub) if ra["points"] > rb["points"] else (ub, ua)
                wp = max(ra["points"], rb["points"])
                lp = min(ra["points"], rb["points"])
                if margin > 0:
                    close.append((margin, season, week, win, lose, wp, lp))
                    blowout.append((margin, season, week, win, lose, wp, lp))
                unlucky.append((lp, season, week, lose, win, lp, wp))
                lucky.append((-wp, season, week, win, lose, wp, lp))
                shootout.append((ra["points"] + rb["points"], season, week, ua, ub, ra["points"], rb["points"]))

    for margin, season, week, win, lose, wp, lp in sorted(close)[:8]:
        # Two decimals here specifically: the tightest games are decided by hundredths, and
        # rounding to one made a genuine 0.04 point win read as "by 0.0", i.e. as a tie.
        fact(
            "closest_game",
            f"{handle(win)} beat {handle(lose)} by {margin:.2f} in week {week} of {season}, {wp:.2f} to {lp:.2f}.",
            season=season, week=week, managers=[win, lose], margin=margin, winner_points=wp, loser_points=lp,
        )

    for margin, season, week, win, lose, wp, lp in sorted(blowout, reverse=True)[:8]:
        fact(
            "biggest_blowout",
            f"{handle(win)} buried {handle(lose)} by {r1(margin)} in week {week} of {season}, {r1(wp)} to {r1(lp)}.",
            season=season, week=week, managers=[win, lose], margin=margin, winner_points=wp, loser_points=lp,
        )

    for lp, season, week, lose, win, _, wp in sorted(unlucky, reverse=True)[:6]:
        fact(
            "unluckiest_loss",
            f"{handle(lose)} scored {r1(lp)} in week {week} of {season} and still lost, because "
            f"{handle(win)} went for {r1(wp)}.",
            season=season, week=week, managers=[lose, win], points=lp, opponent_points=wp,
        )

    for negwp, season, week, win, lose, wp, lp in sorted(lucky, reverse=True)[:6]:
        fact(
            "luckiest_win",
            f"{handle(win)} won week {week} of {season} with just {r1(wp)} -- {handle(lose)} managed only {r1(lp)}.",
            season=season, week=week, managers=[win, lose], points=wp, opponent_points=lp,
        )

    for total, season, week, ua, ub, pa, pb in sorted(shootout, reverse=True)[:5]:
        fact(
            "highest_scoring_matchup",
            f"{handle(ua)} and {handle(ub)} combined for {r1(total)} in week {week} of {season} "
            f"({r1(pa)} to {r1(pb)}).",
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
            legs.append((week, row["points"], handle(opp), WEEKS[season][week][opp]["points"]))
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
                        mine = ra if ua == user else rb
                        theirs = rb if ua == user else ra
                        if mine["points"] != theirs["points"]:
                            seq.append((season, week, mine["points"] > theirs["points"]))
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
    tally = defaultdict(lambda: [0, 0, 0.0, 0.0])
    for season in played_seasons():
        for week in league_weeks(season):
            for ua, ra, ub, rb in matchups(season, week):
                key = tuple(sorted((ua, ub)))
                first = key[0]
                a, b = (ra, rb) if ua == first else (rb, ra)
                rec = tally[key]
                rec[2] += a["points"]
                rec[3] += b["points"]
                if a["points"] > b["points"]:
                    rec[0] += 1
                elif b["points"] > a["points"]:
                    rec[1] += 1
    for (ua, ub), (wa, wb, pa, pb) in sorted(tally.items(), key=lambda kv: -(kv[1][0] + kv[1][1])):
        if wa + wb == 0:
            continue
        lead = handle(ua) if wa >= wb else handle(ub)
        fact(
            "head_to_head",
            f"{handle(ua)} and {handle(ub)} have met {wa + wb} times: {wa}-{wb} to {lead}, "
            f"{r1(pa)} against {r1(pb)} all told.",
            managers=[ua, ub], wins_first=wa, wins_second=wb, points_first=pa, points_second=pb,
        )


def derive_season_swings():
    for user, m in MANAGERS.items():
        recs = {s: r for s, r in m.get("records", {}).items() if r["wins"] + r["losses"] + r["ties"] > 0}
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

def season_points_by_player(season):
    tally = defaultdict(float)
    for week, wk in week_rows(season):
        for user, row in wk.items():
            for pid, pts in row.get("players_points", {}).items():
                tally[str(pid)] += pts
    return tally


def derive_draft_value():
    for season in played_seasons():
        drafts = [d for d in HISTORY["drafts"].get(season, []) if d.get("primary")]
        if not drafts:
            continue
        # Keepers occupy a draft slot but were never a draft decision, so they are not steals or
        # busts -- they are keeper decisions, and best_keeper/worst_keeper already tell that
        # story. Without this filter mikestreinz's 2024 "round 1 pick" on Christian McCaffrey
        # appeared as a draft bust and again, correctly, as a failed keeper.
        picks = [p for p in drafts[0]["picks"] if not p.get("is_keeper")]
        pts = season_points_by_player(season)
        scored = [(pts.get(str(p["player_id"]), 0.0), p) for p in picks if p.get("player_id")]

        late = [(v, p) for v, p in scored if p["round"] >= 8]
        if late:
            v, p = max(late, key=lambda x: x[0])
            fact(
                "draft_steal",
                f"{pname(p['player_id'])} went in round {p['round']} of the {season} draft to "
                f"{handle(p.get('picked_by'))} and scored {r1(v)} that season.",
                season=season, managers=[p.get("picked_by")], players=[p["player_id"]],
                round=p["round"], points=v,
            )

        early = [(v, p) for v, p in scored if p["round"] <= 3]
        if early:
            v, p = min(early, key=lambda x: x[0])
            fact(
                "draft_bust",
                f"{handle(p.get('picked_by'))} spent a round {p['round']} pick on "
                f"{pname(p['player_id'])} in {season} and got {r1(v)} points.",
                season=season, managers=[p.get("picked_by")], players=[p["player_id"]],
                round=p["round"], points=v,
            )


def derive_keeper_value():
    rows = []
    for season, entries in KEEPERS.items():
        if season not in WEEKS or not WEEKS[season]:
            continue
        pts = season_points_by_player(season)
        for k in entries:
            rows.append((pts.get(str(k["player_id"]), 0.0), season, k))
    for v, season, k in sorted(rows, reverse=True)[:6]:
        fact(
            "best_keeper",
            f"{handle(k['user_id'])} kept {pname(k['player_id'])} at a round {k['cost_round']} cost "
            f"in {season}; he returned {r1(v)} points.",
            season=season, managers=[k["user_id"]], players=[k["player_id"]],
            cost_round=k["cost_round"], points=v,
        )
    for v, season, k in sorted(rows)[:5]:
        fact(
            "worst_keeper",
            f"{handle(k['user_id'])} kept {pname(k['player_id'])} at a round {k['cost_round']} cost "
            f"in {season} and got {r1(v)} points out of him.",
            season=season, managers=[k["user_id"]], players=[k["player_id"]],
            cost_round=k["cost_round"], points=v,
        )


def points_after(season, week, user, pid):
    """
    What a player scored FOR THIS MANAGER from the pickup onward.

    Season totals are the wrong measure of a waiver bid: paulslaats paid $75 for Trevor
    Lawrence in week 16 of 2022, and quoting the full-season figure credits him with points
    scored for somebody else in weeks 1 to 15.
    """
    if season not in WEEKS or not WEEKS[season] or week is None:
        return 0.0
    total = 0.0
    for w, rows in week_rows(season):
        if int(w) < int(week):
            continue
        row = rows.get(user)
        if row:
            total += row.get("players_points", {}).get(str(pid), 0.0)
    return total


def derive_money():
    spends = []
    for t in TRANSACTIONS:
        if t.get("status") != "complete" or not t.get("faab"):
            continue
        adds = t.get("adds") or {}
        for pid, user in adds.items():
            spends.append((t["faab"], t["season"], t.get("week"), user, pid))
    for amount, season, week, user, pid in sorted(spends, reverse=True)[:8]:
        pts = points_after(season, week, user, pid)
        fact(
            "faab_splurge",
            f"{handle(user)} spent ${amount} of FAAB on {pname(pid)} in week {week} of {season}. "
            f"He scored {r1(pts)} for him after that.",
            season=season, week=week, managers=[user], players=[pid], faab=amount, points=pts,
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
        f"{len(FACTS)} facts across seasons {', '.join(played_seasons())}.",
        "",
    ]
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


if __name__ == "__main__":
    main()
