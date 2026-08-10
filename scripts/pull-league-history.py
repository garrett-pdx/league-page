#!/usr/bin/env python3
"""
Pull the full history of the Mudd League out of Sleeper into static/data/.

    python3 scripts/pull-league-history.py

Walks previous_league_id back from the current season, so it needs no season
list -- only CURRENT_LEAGUE_ID below. Roughly 300 requests, ~1-2 minutes.

Outputs (all documented in static/data/README.md):
    league-history.json   seasons, managers, records, drafts, brackets
    transactions.json     every add/drop/waiver/trade, manager-resolved
    weeks.json            WEEKLY ROSTER SNAPSHOTS -- the time machine
    ownership.json        player_id -> spans of who rostered them, when
    keepers.json          keeper chains, cost in rounds, inflation
    players.json          player_id -> {n: name, p: position, t: team}

Sleeper's API is public, read-only and unauthenticated. Re-run after a season
ends (or whenever) and commit the diff.
"""
import json, os, sys, time, urllib.request, urllib.error
from collections import defaultdict
from datetime import datetime, timezone

CURRENT_LEAGUE_ID = "1312235880743706624"
BASE = "https://api.sleeper.app/v1"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "static", "data")


def get(path, retries=3):
    url = f"{BASE}/{path}"
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if attempt == retries - 1:
                raise
            time.sleep(1 + attempt)
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(1 + attempt)
    return None


def fetch_seasons():
    chain, lid = [], CURRENT_LEAGUE_ID
    while lid and lid != "0":
        league = get(f"league/{lid}")
        if not league:
            break
        chain.append(league)
        lid = league.get("previous_league_id")
    chain.reverse()
    return chain


def fetch_all(chain):
    raw = {}
    for league in chain:
        lid, season = league["league_id"], league["season"]
        print(f"  {season} ...", end="", flush=True)
        last_week = (league["settings"].get("playoff_week_start") or 15) + 4
        node = {
            "league": league,
            "users": get(f"league/{lid}/users") or [],
            "rosters": get(f"league/{lid}/rosters") or [],
            "winners_bracket": get(f"league/{lid}/winners_bracket") or [],
            "losers_bracket": get(f"league/{lid}/losers_bracket") or [],
            "traded_picks": get(f"league/{lid}/traded_picks") or [],
            "drafts": get(f"league/{lid}/drafts") or [],
            "transactions": {}, "matchups": {}, "draft_picks": {},
        }
        for d in node["drafts"]:
            node["draft_picks"][d["draft_id"]] = get(f"draft/{d['draft_id']}/picks") or []
            time.sleep(0.08)
        ntx = 0
        for wk in range(1, last_week + 1):
            tx = get(f"league/{lid}/transactions/{wk}") or []
            if tx:
                node["transactions"][str(wk)] = tx
                ntx += len(tx)
            mu = get(f"league/{lid}/matchups/{wk}") or []
            if mu and any(m.get("players") for m in mu):
                node["matchups"][str(wk)] = mu
            time.sleep(0.08)
        print(f" {ntx} transactions, {len(node['matchups'])} played weeks")

        # A failed users/rosters fetch degrades to [] and would otherwise sail
        # through: the season would end up with an empty roster map, no records,
        # no weekly snapshots, and every transaction resolving to None managers --
        # silently, with a zero exit code. Refuse to write a corrupt dataset.
        expected = league["settings"].get("num_teams")
        if not node["users"] or not node["rosters"]:
            raise SystemExit(f"{season}: users/rosters came back empty -- aborting rather "
                             f"than writing a season with no managers")
        if expected and len(node["rosters"]) != expected:
            raise SystemExit(f"{season}: expected {expected} rosters, got "
                             f"{len(node['rosters'])} -- aborting rather than writing "
                             f"a partial season")
        raw[season] = node
    return raw


def resolve_players(raw):
    ids = set()
    for node in raw.values():
        for txs in node["transactions"].values():
            for t in txs:
                ids.update((t.get("adds") or {}).keys())
                ids.update((t.get("drops") or {}).keys())
        for mus in node["matchups"].values():
            for m in mus:
                ids.update(m.get("players") or [])
                ids.update(m.get("starters") or [])
        for r in node["rosters"]:
            ids.update(r.get("keepers") or [])
        for picks in node["draft_picks"].values():
            for p in picks:
                if p.get("player_id"):
                    ids.add(p["player_id"])
    ids.discard(None)
    ids.discard("0")
    print(f"  resolving {len(ids)} player ids (~5MB dictionary)")
    allp = get("players/nfl") or {}
    slim = {}
    for pid in ids:
        p = allp.get(str(pid))
        if not p:
            continue
        name = p.get("full_name") or f"{p.get('first_name','')} {p.get('last_name','')}".strip() or str(pid)
        slim[str(pid)] = {"n": name, "p": p.get("position"), "t": p.get("team")}
    print(f"  resolved {len(slim)}")
    return slim


def build(raw, players):
    managers, season_meta, drafts_out, brackets_out = {}, {}, {}, {}
    ledger, weeks, traded_picks = [], {}, {}
    records, roster_keepers = defaultdict(dict), defaultdict(dict)
    # (season, week) -> {player_id: user_id}, used for ownership + keeper lineage
    owner_at = {}

    for season in sorted(raw):
        d = raw[season]
        lg, users = d["league"], {u["user_id"]: u for u in d["users"]}
        r2u = {r["roster_id"]: r.get("owner_id") for r in d["rosters"]}
        rostered = {r.get("owner_id") for r in d["rosters"] if r.get("owner_id")}

        season_meta[season] = {
            "league_id": lg["league_id"], "name": lg["name"], "status": lg["status"],
            "teams": lg["settings"].get("num_teams"),
            "playoff_teams": lg["settings"].get("playoff_teams"),
            "playoff_week_start": lg["settings"].get("playoff_week_start"),
            "waiver_budget": lg["settings"].get("waiver_budget"),
            "max_keepers": lg["settings"].get("max_keepers"),
            "roster_positions": lg["roster_positions"],
            "users_without_roster": [users[u]["display_name"] for u in users if u not in rostered],
            "weeks_played": sorted(int(w) for w in d["matchups"]),
        }

        for uid, u in users.items():
            m = managers.setdefault(uid, {"handle": u.get("display_name"), "seasons": [],
                                          "seasons_rostered": [], "team_names": []})
            m["handle"] = u.get("display_name") or m["handle"]
            m["seasons"].append(season)
            if uid in rostered:
                m["seasons_rostered"].append(season)
            tn = (u.get("metadata") or {}).get("team_name")
            if tn and tn not in m["team_names"]:
                m["team_names"].append(tn)

        for r in d["rosters"]:
            uid = r.get("owner_id")
            if not uid:
                continue
            st = r["settings"]
            records[uid][season] = {
                "roster_id": r["roster_id"],
                "wins": st.get("wins"), "losses": st.get("losses"), "ties": st.get("ties"),
                "points_for": round(st.get("fpts", 0) + st.get("fpts_decimal", 0) / 100, 2),
                "points_against": round(st.get("fpts_against", 0) + st.get("fpts_against_decimal", 0) / 100, 2),
                "potential_points": round(st.get("ppts", 0) + st.get("ppts_decimal", 0) / 100, 2),
                "waiver_budget_used": st.get("waiver_budget_used"),
                "waiver_position": st.get("waiver_position"),
            }
            if r.get("keepers"):
                roster_keepers[uid][season] = r["keepers"]

        for dr in d["drafts"]:
            drafts_out.setdefault(season, []).append({
                "draft_id": dr["draft_id"], "type": dr["type"], "status": dr["status"],
                "rounds": dr["settings"].get("rounds"),
                "created": dr.get("created"), "start_time": dr.get("start_time"),
                "primary": False,
                "picks": [{"round": p["round"], "pick_no": p["pick_no"],
                           "draft_slot": p["draft_slot"], "player_id": p.get("player_id"),
                           "picked_by": p.get("picked_by"), "roster_id": p.get("roster_id"),
                           "is_keeper": bool(p.get("is_keeper"))}
                          for p in d["draft_picks"].get(dr["draft_id"], [])],
            })
        # 2022 has TWO drafts attached to the same league. The 14-round one that started
        # 2022-09-04 and carries the keeper flags is the real 2022 season draft. The
        # 15-round one dated 2022-06-25 is NOT a 2022 draft at all -- it is the previous
        # season's draft, carried over from the league's earlier home on another platform
        # and re-uploaded here, which is why 2022's keeper costs price off it. The
        # latest-starting draft is always the season's real one.
        ds = drafts_out.get(season) or []
        if ds:
            latest = max(ds, key=lambda x: (x.get("start_time") or x.get("created") or 0))
            latest["primary"] = True

        brackets_out[season] = {"winners": d["winners_bracket"], "losers": d["losers_bracket"]}

        # Pick ownership is filed on the league that was current when the trade happened,
        # but the `season` field says which draft the pick is FOR. Resolve both the
        # original and current owner to user_ids using THIS season's roster map.
        for tp in d["traded_picks"]:
            traded_picks.setdefault(tp["season"], []).append({
                "round": tp["round"],
                "original_owner": r2u.get(tp["roster_id"]),
                "current_owner": r2u.get(tp["owner_id"]),
                "previous_owner": r2u.get(tp.get("previous_owner_id")),
                "recorded_on_season": season,
            })

        # ---- weekly roster snapshots: the time machine ----------------------
        weeks[season] = {}
        for wk, mus in d["matchups"].items():
            snap, owners = {}, {}
            for m in mus:
                uid = r2u.get(m["roster_id"])
                if not uid:
                    continue
                snap[uid] = {
                    "roster_id": m["roster_id"],
                    "matchup_id": m.get("matchup_id"),
                    "points": m.get("points"),
                    "starters": m.get("starters") or [],
                    "starters_points": m.get("starters_points") or [],
                    "players": m.get("players") or [],
                    "players_points": m.get("players_points") or {},
                }
                for pid in (m.get("players") or []):
                    owners[str(pid)] = uid
            weeks[season][wk] = snap
            owner_at[(season, int(wk))] = owners

        for wk, txs in d["transactions"].items():
            for t in txs:
                ledger.append({
                    "season": season, "week": int(t.get("leg") or wk),
                    # keep the id: two genuinely distinct Sleeper transactions can
                    # collapse to identical rows once the timestamp is truncated to a
                    # date, so without this a consumer deduping by content would drop
                    # a real event (seen in 2022 -- same player added twice, 17h apart)
                    "transaction_id": t["transaction_id"],
                    "date": datetime.fromtimestamp(t["created"] / 1000, tz=timezone.utc).strftime("%Y-%m-%d"),
                    "type": t["type"], "status": t["status"],
                    "faab": (t.get("settings") or {}).get("waiver_bid"),
                    "adds": {pid: r2u.get(rid) for pid, rid in (t.get("adds") or {}).items()},
                    "drops": {pid: r2u.get(rid) for pid, rid in (t.get("drops") or {}).items()},
                    "managers": [r2u.get(r) for r in (t.get("roster_ids") or [])],
                    "faab_transfers": t.get("waiver_budget") or [],
                    "draft_picks": t.get("draft_picks") or [],
                })

    ledger.sort(key=lambda e: (e["season"], e["week"], e["date"]))

    for uid, m in managers.items():
        m["records"] = records.get(uid, {})
        m["roster_keepers"] = roster_keepers.get(uid, {})
        rs = list(m["records"].values())
        m["career"] = {
            "seasons_played": len(m["seasons_rostered"]),
            "wins": sum(r["wins"] or 0 for r in rs),
            "losses": sum(r["losses"] or 0 for r in rs),
            "ties": sum(r["ties"] or 0 for r in rs),
            "points_for": round(sum(r["points_for"] for r in rs), 2),
            "points_against": round(sum(r["points_against"] for r in rs), 2),
        }

    standings = build_standings(brackets_out, records)
    ownership = build_ownership(owner_at)
    keepers = build_keepers(drafts_out, owner_at, ownership)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return {
        "league-history.json": {"generated": today, "seasons": season_meta,
                                "managers": managers, "drafts": drafts_out,
                                "brackets": brackets_out, "final_standings": standings,
                                "traded_picks": traded_picks},
        "transactions.json": {"generated": today, "count": len(ledger), "transactions": ledger},
        "weeks.json": {"generated": today, "weeks": weeks},
        "ownership.json": {"generated": today, "ownership": ownership},
        "keepers.json": {"generated": today, "keepers": keepers},
        "players.json": players,
    }


def build_standings(brackets_out, records):
    """
    Final placement per season, derived from the playoff brackets.

    Sleeper marks placement games with `p`: in the winners bracket p=1 is the title
    game (winner 1st, loser 2nd) and p=3 the third-place game. The losers bracket
    repeats the pattern for the consolation places, so its p=1 game decides 5th/6th.
    The two teams in neither bracket finish 9th and 10th -- second to last and last --
    ordered by regular-season record, then points for. Sleeper never assigns them a
    placement, so that ordering is ours; it is how the league reckons it.
    """
    out = {}
    for season, br in brackets_out.items():
        r2u = {}
        for uid, seasons in records.items():
            rec = seasons.get(season)
            if not rec:
                continue
            rid = rec["roster_id"]
            # a dict comprehension here would silently drop one of the two on a
            # collision, resolving a bracket placement to the wrong manager
            if rid in r2u:
                raise SystemExit(f"{season}: roster_id {rid} maps to two managers "
                                 f"({r2u[rid]} and {uid}) -- cannot resolve standings")
            r2u[rid] = uid
        place = {}
        for bracket, base in ((br.get("winners") or [], 1), (br.get("losers") or [], 5)):
            for g in bracket:
                p = g.get("p")
                if p is None or g.get("w") is None:
                    continue
                place[base + p - 1] = g["w"]
                place[base + p] = g.get("l")
        # No completed bracket means the season hasn't been played out. Emit nothing
        # rather than ranking ten 0-0 teams against each other and inventing a champion.
        if not place:
            continue
        placed = {r for r in place.values() if r is not None}
        rest = [r for r in r2u if r not in placed]
        rest.sort(key=lambda r: (-(records[r2u[r]][season]["wins"] or 0),
                                 -records[r2u[r]][season]["points_for"]))
        rows = []
        for pos in sorted(place):
            if place[pos] is not None:
                rows.append({"place": pos, "user_id": r2u.get(place[pos]), "source": "bracket"})
        nxt = (max(place) + 1) if place else 1
        for i, r in enumerate(rest):
            rows.append({"place": nxt + i, "user_id": r2u.get(r), "source": "regular season"})
        if rows:
            out[season] = rows
    return out


def build_ownership(owner_at):
    """player_id -> [{u, s, w0, w1}] run-length spans of continuous ownership."""
    keys = sorted(owner_at, key=lambda k: (k[0], k[1]))
    spans = defaultdict(list)
    for season, wk in keys:
        for pid, uid in owner_at[(season, wk)].items():
            runs = spans[pid]
            if runs and runs[-1]["u"] == uid and runs[-1]["s"] == season and runs[-1]["w1"] == wk - 1:
                runs[-1]["w1"] = wk
            else:
                runs.append({"u": uid, "s": season, "w0": wk, "w1": wk})
    return spans


def build_keepers(drafts_out, owner_at, ownership):
    """
    Every kept player, per season, with cost and lineage.

    A keeper occupies the pick slot it costs, so the pick's ROUND is the cost.
    Lineage comes from the weekly snapshots: who held this player in the final
    played week of the previous season, and was he kept that year too.
    """
    last_week_of = {}
    for (season, wk) in owner_at:
        last_week_of[season] = max(last_week_of.get(season, 0), wk)

    def primary(season):
        ds = [d for d in drafts_out.get(season, []) if d.get("primary")]
        return ds[0] if ds else (drafts_out.get(season) or [None])[0]

    # what round each player occupied in a season's PRIMARY draft
    round_in = {}
    rounds_of = {}
    kept_in = defaultdict(set)
    # carried[season] = rounds from an earlier, non-primary draft filed under the SAME
    # season. For 2022 that is the previous season's draft imported from the league's
    # earlier home on another platform -- the only surviving record of that year, and the
    # baseline 2022's keeper costs were priced from.
    carried = {}
    for season in drafts_out:
        dr = primary(season)
        if not dr:
            continue
        rounds_of[season] = dr["rounds"]
        for p in dr["picks"]:
            if p.get("player_id"):
                round_in[(season, str(p["player_id"]))] = p["round"]
                if p["is_keeper"]:
                    kept_in[season].add(str(p["player_id"]))
        others = [x for x in drafts_out[season] if not x.get("primary") and x["picks"]]
        if others:
            earliest = min(others, key=lambda x: (x.get("start_time") or x.get("created") or 0))
            carried[season] = {str(p["player_id"]): p["round"]
                               for p in earliest["picks"] if p.get("player_id")}

    out = {}
    for season in sorted(drafts_out):
        prev = str(int(season) - 1)
        prev_owners = owner_at.get((prev, last_week_of.get(prev, 0)), {})
        dr = primary(season)
        if not dr:
            continue
        rows = []
        for p in dr["picks"]:
            if not p["is_keeper"] or not p.get("player_id"):
                continue
            pid = str(p["player_id"])
            keeper_uid = p.get("picked_by")
            prior = prev_owners.get(pid)
            same = bool(prior and keeper_uid and prior == keeper_uid)
            chained = pid in kept_in.get(prev, set())
            prior_round = round_in.get((prev, pid))
            baseline = "previous season"
            if prior_round is None and pid in carried.get(season, {}):
                # priced off the imported prior-season draft (see note above)
                prior_round = carried[season][pid]
                baseline = "carried-over prior-season draft"
            # constitution 4.2/4.3/4.4: cost = prior-year round, -1 if the same manager
            # keeps him again, floored at R1; undrafted last year costs the final round.
            if prior_round is None:
                expected = rounds_of.get(season)
            else:
                expected = max(1, prior_round - 1) if (same and chained) else prior_round
                if rounds_of.get(season):
                    expected = min(expected, rounds_of[season])
            rows.append({
                "player_id": pid,
                "user_id": keeper_uid,
                "round": p["round"],
                "pick_no": p["pick_no"],
                "cost_round": p["round"],
                "previous_season_round": prior_round,
                "baseline": baseline,
                "expected_cost_round": expected,
                "matches_rule": expected == p["round"],
                "held_previous_season_by": prior,
                "same_manager_as_last_season": same,
                "kept_previous_season_too": chained,
            })
        if rows:
            out[season] = sorted(rows, key=lambda r: r["pick_no"])
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    print("walking league chain...")
    chain = fetch_seasons()
    if not chain:
        print("could not reach Sleeper", file=sys.stderr)
        return 1
    print(f"seasons: {', '.join(c['season'] for c in chain)}")
    raw = fetch_all(chain)
    players = resolve_players(raw)
    outputs = build(raw, players)
    print()
    for name, payload in outputs.items():
        path = os.path.join(OUT, name)
        with open(path, "w") as f:
            json.dump(payload, f, separators=(",", ":"))
        print(f"  wrote {name:<24}{round(os.path.getsize(path)/1024):>5} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
