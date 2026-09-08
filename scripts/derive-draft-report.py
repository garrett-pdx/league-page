#!/usr/bin/env python3
"""
Derive the preseason draft report: what the 2026 draft did, and where it leaves everyone.

Writes static/data/draft-2026.json (the facts block) and docs/draft-2026.md (a prose
skeleton). Same contract as derive-narratives.py: this is an AUTHORING AID. Nothing in
src/ fetches either file and nothing should. Every number a published article asserts must
appear in the facts block, so a claim can always be traced back to a computation.

Two market baselines, used for deliberately different jobs. Mixing them up would be the
easiest way to produce a confident wrong answer:

  * GRADING A PICK uses the FROZEN snapshot in the keeper-draft-board repo, captured
    2026-08-22 -- one day before this draft. That is the market as it stood at the buzzer,
    which is the only fair thing to judge a pick against. It carries ordinal ranks only,
    which is fine here: a pick is itself an ordinal (pick 37 against rank 21).

  * RANKING A ROSTER uses LIVE FantasyCalc values, which are cardinal (Gibbs 10348, not
    "rank 1"). Ranks must never be summed -- the gap between ranks 1 and 10 dwarfs the gap
    between 100 and 110, so adding them up silently flatters deep, mediocre rosters. Cardinal
    values are also simply the right measure of "how good is this roster today", 16 days and
    14 transactions after the draft.

The keeper-draft-board repo is a separate project (see the root CLAUDE.md: the two share a
league, not a codebase). We read two of its snapshot files and copy what we use into our own
output, so the report stays reproducible without it. We do not import its code.

Run:  python3 scripts/derive-draft-report.py
"""

import json
import os
import re
import sys
import urllib.request
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "static", "data")
DOCS = os.path.join(ROOT, "docs")

# Separate repo, deliberately referenced by path rather than imported or vendored wholesale.
BOARD = os.path.expanduser("~/Desktop/ff_keeper/public")

SEASON = "2026"
LEAGUE_ID = "1312235880743706624"
FANTASYCALC = "https://api.fantasycalc.com/values/current?isDynasty=false&numQbs=1&numTeams=10&ppr=0.5"
ROSTERS_URL = f"https://api.sleeper.app/v1/league/{LEAGUE_ID}/rosters"

# The league's starting lineup. Bench depth is real but it is not what wins a week, so the
# ranking weighs starters and counts the bench separately rather than lumping them together.
STARTER_SLOTS = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX"]
FLEX_OK = {"RB", "WR", "TE"}


def load(path):
    with open(path) as f:
        return json.load(f)


def get_json(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read())


HISTORY = load(os.path.join(DATA, "league-history.json"))
KEEPERS = load(os.path.join(DATA, "keepers.json"))["keepers"]
WEEKS = load(os.path.join(DATA, "weeks.json"))["weeks"]
PLAYERS = load(os.path.join(DATA, "players.json"))
STANDINGS = HISTORY.get("final_standings", {})
MANAGERS = HISTORY["managers"]


def real_names():
    """
    managerID -> real name, read out of leagueInfo.js.

    Parsed rather than hardcoded so a name change in the config cannot silently desync the
    report. leagueInfo.js is JS, not JSON, so this is a regex over a stable hand-written
    shape; it is checked below and the script refuses to run on a partial match.
    """
    src = open(os.path.join(ROOT, "src", "lib", "utils", "leagueInfo.js")).read()
    pairs = re.findall(
        r'"managerID":\s*"(\d+)",\s*\n\s*"name":\s*"([^"]+)"', src
    )
    return {mid: name for mid, name in pairs}


NAMES = real_names()


def name(user_id):
    if user_id in NAMES:
        return NAMES[user_id]
    return MANAGERS.get(user_id, {}).get("handle", str(user_id))


def handle(user_id):
    return MANAGERS.get(user_id, {}).get("handle", str(user_id))


# ---------------------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------------------

def draft_picks(season):
    drafts = [d for d in HISTORY["drafts"].get(season, []) if d.get("primary")]
    if not drafts:
        return []
    return drafts[0].get("picks", [])


def frozen_baseline():
    """The Aug 22 snapshots: FantasyCalc ordinal ranks, and real-league ADP."""
    vpath = os.path.join(BOARD, "value-snapshot.json")
    apath = os.path.join(BOARD, "adp-real-snapshot.json")
    if not (os.path.exists(vpath) and os.path.exists(apath)):
        print(
            f"missing draft-day snapshots under {BOARD}\n"
            "  These live in the keeper-draft-board repo and are the only fair baseline for\n"
            "  grading picks. Clone/refresh it, or re-run once it is present.",
            file=sys.stderr,
        )
        sys.exit(1)

    v = load(vpath)
    cfg = next(
        e for e in v["entries"]
        if e["numQbs"] == 1 and e["numTeams"] == 10 and e["ppr"] == 0.5
    )
    vrank = {str(p["id"]): p["rank"] for p in cfg["players"]}

    a = load(apath)
    adp = {}
    for entry in a["entries"]:
        for p in entry["players"]:
            adp[norm(p["name"])] = p["adp"]

    return {
        "value_rank": vrank,
        "value_fetched_at": v.get("fetchedAt"),
        "value_attribution": v.get("attribution"),
        "adp_by_name": adp,
        "adp_fetched_at": a.get("fetchedAt"),
        "adp_attribution": a.get("attribution"),
        "adp_excludes": sorted(
            {p for e in a["entries"] for p in (e["meta"].get("excludedPositions") or [])}
        ),
    }


def norm(s):
    return re.sub(r"[^a-z]", "", (s or "").lower())


def live_values():
    """Cardinal values, today. Keyed by Sleeper id so no name matching is involved."""
    raw = get_json(FANTASYCALC)
    out = {}
    for row in raw:
        sid = row.get("player", {}).get("sleeperId")
        if sid:
            out[str(sid)] = {
                "value": row.get("value"),
                "rank": row.get("overallRank"),
                "position_rank": row.get("positionRank"),
                "name": row["player"].get("name"),
                "position": row["player"].get("position"),
            }
    return out


# ---------------------------------------------------------------------------------------
# Draft analysis -- graded against the frozen, draft-day market
# ---------------------------------------------------------------------------------------

def pick_name(p):
    """
    Player name for a pick.

    The live Sleeper draft feed carries a `metadata` block with first/last name, but
    pull-league-history.py deliberately stores a lean pick and resolves identity through
    players.json instead -- the same {n, p, t} lookup derive-narratives.py uses. Reading
    metadata here silently yielded raw ids, which then matched nothing in the ADP feed and
    emptied the positional tables.
    """
    return PLAYERS.get(str(p.get("player_id")), {}).get("n") or str(p.get("player_id"))


def pick_position(p):
    return PLAYERS.get(str(p.get("player_id")), {}).get("p")


def analyse_picks(picks, base):
    """
    Per-pick delta against the draft-day market.

    Keepers are excluded: a kept player occupies a slot but was not a live draft-day
    decision, so grading one grades last year's choice. Same filter and reasoning as
    derive-narratives.py's derive_draft_value() and analyze-draft-positions.py.
    """
    vrank = base["value_rank"]
    adp = base["adp_by_name"]
    rows = []
    for p in picks:
        if p.get("is_keeper"):
            continue
        pid = str(p.get("player_id") or "")
        rank = vrank.get(pid)
        a = adp.get(norm(pick_name(p)))
        rows.append({
            "pick_no": p["pick_no"],
            "round": p["round"],
            "user_id": p.get("picked_by"),
            "manager": name(p.get("picked_by")),
            "player_id": pid,
            "player": pick_name(p),
            "position": pick_position(p),
            "market_rank": rank,
            # Raw overall-rank delta. Kept for reference but NOT used to pick steals and
            # reaches -- see grade_within_position() for why it cannot be.
            "value_delta": (p["pick_no"] - rank) if rank is not None else None,
            "adp": a,
            "adp_delta": (p["pick_no"] - a) if a is not None else None,
        })
    grade_within_position(rows)
    return rows


def grade_within_position(rows):
    """
    Grade each pick against the market's ordering OF HIS OWN POSITION.

    Comparing an overall trade-value rank to a pick number looks right and is badly wrong in
    a one-QB league. FantasyCalc ranks on trade value, where a quarterback is cheap because
    only one starts and replacements are abundant -- so QBs sit far down the overall list
    while still being drafted in the middle rounds by ten managers who each must start one.
    Scored that way, the first cut of this report returned seven quarterbacks in an
    eight-row "steals" table: Jalen Hurts at pick 84 against overall rank 57 is not a steal,
    it is the shape of the positional value curve.

    Within a position that distortion cancels out. If the market's third-best available
    running back went eleventh among running backs, that is a real reach, in units nobody
    can misread.
    """
    by_pos = defaultdict(list)
    for r in rows:
        if r["position"] and r["market_rank"] is not None:
            by_pos[r["position"]].append(r)

    for pos, group in by_pos.items():
        draft_order = sorted(group, key=lambda r: r["pick_no"])
        market_order = sorted(group, key=lambda r: r["market_rank"])
        market_slot = {r["player_id"]: i for i, r in enumerate(market_order, 1)}
        for taken_slot, r in enumerate(draft_order, 1):
            r["pos_taken"] = taken_slot
            r["pos_market"] = market_slot[r["player_id"]]
            # Positive = he lasted longer than the market said he should, i.e. a steal.
            # Matches the sign convention of value_delta (pick_no - rank).
            r["pos_delta"] = r["pos_taken"] - r["pos_market"]
            r["pos_pool"] = len(group)


def keeper_rows(picks, base, live):
    """Keeper surplus: what the market says he is worth against the round he cost."""
    vrank = base["value_rank"]
    rows = []
    for p in picks:
        if not p.get("is_keeper"):
            continue
        pid = str(p.get("player_id") or "")
        rank = vrank.get(pid)
        # A round-N keeper notionally costs the Nth pick of that manager's draft; compare
        # against the pick number that round actually consumed.
        cost_pick = p["pick_no"]
        rows.append({
            "round": p["round"],
            "cost_pick_no": cost_pick,
            "user_id": p.get("picked_by"),
            "manager": name(p.get("picked_by")),
            "player": pick_name(p),
            "player_id": pid,
            "position": pick_position(p),
            "market_rank": rank,
            "surplus": (cost_pick - rank) if rank is not None else None,
            "value_now": (live.get(pid) or {}).get("value"),
        })
    return sorted(rows, key=lambda r: -(r["surplus"] or -9999))


def keeper_compliance(season):
    rows = KEEPERS.get(season, [])
    broken = [r for r in rows if not r.get("matches_rule")]
    all_rows = [r for s in KEEPERS for r in KEEPERS[s]]
    return {
        "season_keepers": len(rows),
        "season_breaking_rule": len(broken),
        "alltime_keepers": len(all_rows),
        "alltime_breaking_rule": len([r for r in all_rows if not r.get("matches_rule")]),
    }


def positional_shape(picks, prior_seasons=("2023", "2024", "2025")):
    """
    2026's positional mix against how this league normally drafts.

    The comparison is the point: 'they took five running backs in round one' only means
    something next to what they usually do. Keepers excluded on both sides.
    """
    def mix(ps):
        by_round = defaultdict(lambda: defaultdict(int))
        for p in ps:
            if p.get("is_keeper") or not p.get("player_id"):
                continue
            pos = pick_position(p)
            if not pos:
                continue
            by_round[p["round"]][pos] += 1
        return by_round

    now = mix(picks)
    prior = defaultdict(lambda: defaultdict(int))
    prior_drafts = 0
    for s in prior_seasons:
        ds = [d for d in HISTORY["drafts"].get(s, []) if d.get("primary")]
        if not ds:
            continue
        prior_drafts += 1
        for r, counts in mix(ds[0].get("picks", [])).items():
            for pos, n in counts.items():
                prior[r][pos] += n

    out = []
    for r in sorted(now):
        cur = dict(now[r])
        hist = {k: round(v / prior_drafts, 2) for k, v in prior[r].items()} if prior_drafts else {}
        out.append({"round": r, "2026": cur, "2023_2025_avg": hist})
    return out


# ---------------------------------------------------------------------------------------
# Preseason rankings -- market-led, history as counterpoint
# ---------------------------------------------------------------------------------------

def best_lineup_value(player_ids, live):
    """
    Value of the best legal starting eight, plus what is left on the bench.

    Greedy by descending value into the tightest slots first (dedicated positions before
    FLEX), which is optimal here because every FLEX-eligible position is also a dedicated
    slot -- there is no slot a player can fill that a higher-valued player could not.
    """
    pool = []
    for pid in player_ids:
        v = live.get(str(pid))
        if v and v.get("value") is not None:
            pool.append((v["value"], str(pid), v.get("position")))
    pool.sort(reverse=True)

    used = set()
    starters = []
    for slot in STARTER_SLOTS:
        for val, pid, pos in pool:
            if pid in used:
                continue
            ok = (pos in FLEX_OK) if slot == "FLEX" else (pos == slot)
            if ok:
                used.add(pid)
                starters.append({"player_id": pid, "value": val, "position": pos, "slot": slot})
                break
    bench = [
        {"player_id": pid, "value": val, "position": pos}
        for val, pid, pos in pool if pid not in used
    ]
    return starters, bench


def career_record(user_id):
    """W/L, points per game and finishes across played seasons only."""
    w = l = t = 0
    pts = 0.0
    games = 0
    for season in sorted(WEEKS):
        if season == SEASON:
            continue  # unplayed; see season_played() in derive-narratives.py
        for wk, rows in WEEKS[season].items():
            row = rows.get(user_id)
            if not row or not row.get("matchup_id"):
                continue
            opp = next(
                (r for u, r in rows.items()
                 if u != user_id and r.get("matchup_id") == row["matchup_id"]),
                None,
            )
            if not opp:
                continue
            mine, theirs = row.get("points") or 0, opp.get("points") or 0
            if mine == 0 and theirs == 0:
                continue
            games += 1
            pts += mine
            if mine > theirs:
                w += 1
            elif mine < theirs:
                l += 1
            else:
                t += 1
    finishes = []
    for season, table in STANDINGS.items():
        for entry in table:
            if str(entry.get("user_id")) == str(user_id):
                finishes.append({"season": season, "place": entry.get("place")})
    finishes.sort(key=lambda f: f["season"])
    played = w + l + t
    return {
        "wins": w, "losses": l, "ties": t,
        "win_pct": round(w / played, 3) if played else None,
        "points_per_game": round(pts / games, 1) if games else None,
        "seasons": len({f["season"] for f in finishes}),
        "titles": len([f for f in finishes if f["place"] == 1]),
        "best_finish": min([f["place"] for f in finishes], default=None),
        "finishes": finishes,
    }


def rank_rosters(rosters, live):
    out = []
    for r in rosters:
        uid = r.get("owner_id")
        players = [str(p) for p in (r.get("players") or [])]
        starters, bench = best_lineup_value(players, live)
        starter_value = sum(s["value"] for s in starters)
        out.append({
            "user_id": uid,
            "manager": name(uid),
            "handle": handle(uid),
            "roster_id": r.get("roster_id"),
            "starter_value": starter_value,
            "bench_value": sum(b["value"] for b in bench),
            "starters": starters,
            "bench_depth": len(bench),
            "unvalued_players": len(players) - len(starters) - len(bench),
            "career": career_record(uid),
        })
    out.sort(key=lambda x: -x["starter_value"])
    for i, row in enumerate(out, 1):
        row["market_rank"] = i
    # History counterpoint: where the market's order disagrees with four years of results.
    by_winpct = sorted(
        out, key=lambda x: -(x["career"]["win_pct"] or 0)
    )
    for i, row in enumerate(by_winpct, 1):
        row["history_rank"] = i
        row["rank_gap"] = row["history_rank"] - row["market_rank"]
    return out


# ---------------------------------------------------------------------------------------

def main():
    picks = draft_picks(SEASON)
    if not picks:
        print(
            f"no {SEASON} draft picks in league-history.json.\n"
            "  Run scripts/pull-league-history.py first -- before the draft completes the\n"
            "  entry exists with status pre_draft and zero picks.",
            file=sys.stderr,
        )
        return 1

    if len(NAMES) < 10:
        print(f"only parsed {len(NAMES)} manager names from leagueInfo.js", file=sys.stderr)
        return 1

    print(f"{len(picks)} picks ({len([p for p in picks if p.get('is_keeper')])} keepers)")
    base = frozen_baseline()
    print(f"draft-day baseline: values {base['value_fetched_at']}, adp {base['adp_fetched_at']}")

    live = live_values()
    print(f"live values: {len(live)} players")
    rosters = get_json(ROSTERS_URL)
    print(f"live rosters: {len(rosters)}")

    graded = analyse_picks(picks, base)
    covered = [g for g in graded if g.get("pos_delta") is not None]
    steals = sorted(covered, key=lambda g: -g["pos_delta"])[:8]
    reaches = sorted(covered, key=lambda g: g["pos_delta"])[:8]

    report = {
        "generated": __import__("datetime").date.today().isoformat(),
        "season": SEASON,
        "method": {
            "grading": "frozen market snapshot from the day before the draft (ordinal ranks)",
            "ranking": "live FantasyCalc cardinal values, best legal starting eight",
            "value_baseline_fetched": base["value_fetched_at"],
            "adp_baseline_fetched": base["adp_fetched_at"],
            "adp_excludes_positions": base["adp_excludes"],
            "attribution": [base["value_attribution"], base["adp_attribution"]],
        },
        "coverage": {
            "picks": len(picks),
            "live_picks_graded": len(covered),
            "live_picks_total": len(graded),
            "picks_with_adp": len([g for g in graded if g["adp"] is not None]),
        },
        "steals": steals,
        "reaches": reaches,
        "all_picks": graded,
        "keepers": keeper_rows(picks, base, live),
        "keeper_compliance": keeper_compliance(SEASON),
        "positional_shape": positional_shape(picks),
        "rankings": rank_rosters(rosters, live),
    }

    out_json = os.path.join(DATA, f"draft-{SEASON}.json")
    with open(out_json, "w") as f:
        json.dump(report, f, separators=(",", ":"))
    print(f"wrote {os.path.relpath(out_json, ROOT)}  ({round(os.path.getsize(out_json)/1024)} KB)")

    write_markdown(report)
    return 0


def write_markdown(r):
    L = []
    a = L.append
    a(f"# The {r['season']} draft, and where it leaves everyone\n")
    a(f"_Derived {r['generated']} by `scripts/derive-draft-report.py`. Every number here is "
      f"computed; see `static/data/draft-{r['season']}.json` for the facts block._\n")
    a("## Method\n")
    a(f"- Picks graded against the market **as it stood the day before the draft** "
      f"({r['method']['value_baseline_fetched']}), not today's.")
    a(f"- Rosters ranked on **live** cardinal values, best legal starting eight "
      f"({'/'.join(STARTER_SLOTS)}).")
    a(f"- Graded {r['coverage']['live_picks_graded']} of {r['coverage']['live_picks_total']} "
      f"live picks; {r['coverage']['picks_with_adp']} of {r['coverage']['picks']} also carry "
      f"real-league ADP (that feed excludes {', '.join(r['method']['adp_excludes_positions'])}).\n")

    a("Graded **within position**: an overall trade-value rank against a pick number is\n"
      "meaningless in a one-QB league, where quarterbacks are cheap to trade for and still\n"
      "have to be drafted by all ten teams.\n")

    a("## Steals\n")
    a("| Pick | Player | Manager | Taken | Market had him | Lasted |")
    a("| --- | --- | --- | --- | --- | --- |")
    for s in r["steals"]:
        a(f"| {s['pick_no']} (R{s['round']}) | {s['player']} | {s['manager']} "
          f"| {s['position']}{s['pos_taken']} | {s['position']}{s['pos_market']} "
          f"| +{s['pos_delta']} |")

    a("\n## Reaches\n")
    a("| Pick | Player | Manager | Taken | Market had him | Early by |")
    a("| --- | --- | --- | --- | --- | --- |")
    for s in r["reaches"]:
        a(f"| {s['pick_no']} (R{s['round']}) | {s['player']} | {s['manager']} "
          f"| {s['position']}{s['pos_taken']} | {s['position']}{s['pos_market']} "
          f"| {s['pos_delta']} |")

    kc = r["keeper_compliance"]
    a(f"\n## Keepers\n")
    a(f"{kc['season_keepers']} kept, **{kc['season_breaking_rule']} breaking the cost rule** "
      f"(all-time: {kc['alltime_keepers'] - kc['alltime_breaking_rule']}/{kc['alltime_keepers']} "
      f"clean).\n")
    a("Surplus is the keeper's cost in picks against his overall market rank -- the right\n"
      "comparison here, because a keeper's cost genuinely is a draft slot. One caveat: the\n"
      "single quarterback on this list is flattered by it, for the same one-QB reason the\n"
      "pick grading above avoids overall rank.\n")
    a("| Kept at | Player | Manager | Market rank | Surplus |")
    a("| --- | --- | --- | --- | --- |")
    for k in r["keepers"]:
        a(f"| R{k['round']} (pick {k['cost_pick_no']}) | {k['player']} ({k['position']}) "
          f"| {k['manager']} | {k['market_rank']} | {k['surplus']} |")

    a("\n## Preseason rankings\n")
    a("Market order, with four seasons of results as counterpoint.\n")
    a("| # | Manager | Starter value | Bench | Career W-L | Win % | History rank | Gap |")
    a("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for row in r["rankings"]:
        c = row["career"]
        a(f"| {row['market_rank']} | {row['manager']} | {row['starter_value']:,} "
          f"| {row['bench_value']:,} | {c['wins']}-{c['losses']} | {c['win_pct']} "
          f"| {row['history_rank']} | {row['rank_gap']:+d} |")

    a("\n## Positional shape vs 2023-25\n")
    a("| Round | 2026 | 2023-25 average |")
    a("| --- | --- | --- |")
    for row in r["positional_shape"]:
        cur = ", ".join(f"{k} {v}" for k, v in sorted(row["2026"].items()))
        hist = ", ".join(f"{k} {v}" for k, v in sorted(row["2023_2025_avg"].items()))
        a(f"| {row['round']} | {cur} | {hist} |")

    path = os.path.join(DOCS, f"draft-{r['season']}.md")
    with open(path, "w") as f:
        f.write("\n".join(L) + "\n")
    print(f"wrote {os.path.relpath(path, ROOT)}")


if __name__ == "__main__":
    sys.exit(main())
