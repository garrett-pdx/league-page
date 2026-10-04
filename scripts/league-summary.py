#!/usr/bin/env python3
"""
A league's format in plain terms, straight from Sleeper: roster, scoring, season, playoffs,
waivers, trades, keepers and the draft.

    python3 scripts/league-summary.py               # the league in league/league.json
    python3 scripts/league-summary.py <league_id>   # any league
    python3 scripts/league-summary.py --json        # machine-readable

It exists for the setup skill: drafting a constitution, a home page or a bio starts from these
facts instead of from memory. Every rule it prints is what Sleeper enforces; a league's own
house rules (keeper costs, votes, dues) are not in Sleeper and have to come from the league.
Stdlib only. Needs network.
"""
import json
import os
import sys
import urllib.request
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lineup import SLOT_ELIGIBLE, NON_STARTING  # noqa: E402

API = "https://api.sleeper.app/v1"


def get(path):
    with urllib.request.urlopen(f"{API}/{path}", timeout=30) as r:
        return json.loads(r.read())


LEAGUE_TYPE = {0: "redraft", 1: "keeper", 2: "dynasty"}
WAIVER_TYPE = {0: "rolling waivers", 1: "reverse-standings waivers", 2: "FAAB"}
ROUND_TYPE = {0: "one week per round", 1: "one week per round, with a two-week final",
              2: "two weeks per round"}
SLOT_NAME = {"FLEX": "FLEX (RB/WR/TE)", "WRRB_FLEX": "FLEX (WR/RB)", "REC_FLEX": "FLEX (WR/TE)",
             "SUPER_FLEX": "SUPERFLEX (QB/RB/WR/TE)", "IDP_FLEX": "IDP FLEX (DL/LB/DB)",
             "DEF": "Team defense", "K": "Kicker"}


def per_point(value):
    """0.04 points per passing yard -> '1 point per 25 yards'."""
    if not value:
        return None
    n = 1 / value
    return f"1 point per {round(n) if abs(n - round(n)) < 0.01 else round(n, 1)} yards"


def summarize(league_id):
    lg = get(f"league/{league_id}")
    st, sc = lg["settings"], lg.get("scoring_settings") or {}
    slots = lg.get("roster_positions") or []
    starters = [s for s in slots if s not in NON_STARTING]
    counts = Counter(starters)
    has = set(starters)
    drafts = get(f"league/{league_id}/drafts") or []
    seasons, lid = [], league_id
    while lid and lid != "0":
        node = lg if lid == league_id else get(f"league/{lid}")
        seasons.append(node["season"])
        lid = node.get("previous_league_id")

    rec = sc.get("rec", 0)
    reception = {1.0: "full PPR", 0.5: "half PPR", 0.0: "standard (no points per reception)"}.get(
        rec, f"{rec} points per reception")
    bonuses = {k: v for k, v in sc.items() if k.startswith("bonus_") and v}
    out = {
        "league": {
            "sleeper_name": lg["name"], "league_id": league_id, "season": lg["season"],
            "status": lg["status"], "teams": st.get("num_teams") or lg.get("total_rosters"),
            "type": LEAGUE_TYPE.get(st.get("type"), f"type {st.get('type')}"),
            "best_ball": bool(st.get("best_ball")),
            "sleeper_seasons": sorted(seasons),
        },
        "roster": {
            "starters": [f"{n} x {SLOT_NAME.get(s, s)}" for s, n in counts.items()],
            "bench": slots.count("BN"), "ir": st.get("reserve_slots") or slots.count("IR"),
            "taxi": st.get("taxi_slots") or 0,
            "ir_allows": [k.replace("reserve_allow_", "") for k, v in st.items()
                          if k.startswith("reserve_allow_") and v],
        },
        "scoring": {
            "receptions": reception,
            "te_premium": sc.get("bonus_rec_te") or 0,
            "passing": {"yards": per_point(sc.get("pass_yd")), "td": sc.get("pass_td"),
                        "int": sc.get("pass_int"), "2pt": sc.get("pass_2pt")},
            "rushing_receiving": {"rush_yards": per_point(sc.get("rush_yd")),
                                  "rec_yards": per_point(sc.get("rec_yd")),
                                  "td": sc.get("rush_td"), "rec_td": sc.get("rec_td"),
                                  "first_downs": {k: v for k, v in sc.items() if k.endswith("_fd") and v}},
            "fumble_lost": sc.get("fum_lost"),
            "bonuses": bonuses,
            "kicker": {k: v for k, v in sc.items() if k.startswith(("fgm", "xp", "fgmiss"))} if "K" in has else None,
            "defense": {k: v for k, v in sc.items() if k.startswith(("pts_allow", "def_", "sack", "int", "safe", "blk_kick", "fum_rec", "ff"))} if "DEF" in has else None,
            "idp": {k: v for k, v in sc.items() if k.startswith("idp_")} if has & {"DL", "LB", "DB", "IDP_FLEX"} else None,
        },
        "season": {
            "regular_season_weeks": f"{st.get('start_week') or 1}-{(st.get('playoff_week_start') or 15) - 1}",
            "median_game": bool(st.get("league_average_match")),
            "divisions": [(lg.get("metadata") or {}).get(f"division_{i}") or f"Division {i}"
                          for i in range(1, (st.get("divisions") or 0) + 1)],
        },
        "playoffs": {
            "teams": st.get("playoff_teams"), "start_week": st.get("playoff_week_start"),
            "rounds": ROUND_TYPE.get(st.get("playoff_round_type") or 0),
            "reseed": bool(st.get("playoff_seed_type")),
            "losers_bracket": "consolation bracket" if st.get("playoff_type") else "toilet bowl",
        },
        "transactions": {
            "waivers": WAIVER_TYPE.get(st.get("waiver_type"), f"type {st.get('waiver_type')}"),
            "faab_budget": st.get("waiver_budget") if st.get("waiver_type") == 2 else None,
            "min_bid": st.get("waiver_bid_min") if st.get("waiver_type") == 2 else None,
            "waiver_clear_days": st.get("waiver_clear_days"),
            "trade_deadline_week": st.get("trade_deadline") if (st.get("trade_deadline") or 99) < 99 else None,
            "trade_review_days": st.get("trade_review_days"),
            "veto_votes_needed": st.get("veto_votes_needed"),
            "draft_pick_trading": bool(st.get("pick_trading")),
        },
        "keepers": {"max_keepers": st.get("max_keepers") or 0,
                    "taxi_years": st.get("taxi_years") if st.get("taxi_slots") else None},
        "draft": [{"season": d.get("season"), "type": d.get("type"), "status": d.get("status"),
                   "rounds": (d.get("settings") or {}).get("rounds")} for d in drafts],
    }
    return out


def text(s):
    L, R, S, P, T, K = (s[k] for k in ("league", "roster", "scoring", "playoffs", "transactions", "keepers"))
    lines = [
        f"# {L['sleeper_name']} ({L['season']}, {L['status']})",
        f"- {L['teams']} teams, {L['type']}{', best ball' if L['best_ball'] else ''}. "
        f"Sleeper seasons on record: {', '.join(L['sleeper_seasons'])}.",
        f"- Starters: {', '.join(R['starters'])}. Bench {R['bench']}, IR {R['ir']}"
        + (f", taxi {R['taxi']}" if R['taxi'] else "") + ".",
        f"- Scoring: {S['receptions']}; passing TD {S['passing']['td']}, {S['passing']['yards']}; "
        f"rushing {S['rushing_receiving']['rush_yards']}; INT {S['passing']['int']}; fumble lost {S['fumble_lost']}."
        + (f" TE premium +{S['te_premium']} per catch." if S['te_premium'] else "")
        + (f" Bonuses: {S['bonuses']}." if S['bonuses'] else ""),
        f"- Regular season weeks {s['season']['regular_season_weeks']}"
        + (", plus a weekly game against the league median" if s['season']['median_game'] else "")
        + (f"; divisions: {', '.join(s['season']['divisions'])}" if s['season']['divisions'] else "") + ".",
        f"- Playoffs: {P['teams']} teams from week {P['start_week']}, {P['rounds']}"
        + (", re-seeded each round" if P['reseed'] else "") + f"; losers play a {P['losers_bracket']}.",
        f"- Waivers: {T['waivers']}"
        + (f", ${T['faab_budget']} budget, minimum bid ${T['min_bid']}" if T['faab_budget'] is not None else "")
        + f". Trade deadline: {'week ' + str(T['trade_deadline_week']) if T['trade_deadline_week'] else 'none'}"
        + (f"; trades review {T['trade_review_days']} day(s)" if T['trade_review_days'] else "")
        + ("; draft picks can be traded" if T['draft_pick_trading'] else "") + ".",
    ]
    if K["max_keepers"] and L["type"] == "keeper":
        lines.append(f"- Keepers: up to {K['max_keepers']} per team (costs are a house rule Sleeper does not enforce).")
    for d in s["draft"]:
        lines.append(f"- {d['season']} draft: {d['rounds']} rounds, {d['type']}, {d['status']}.")
    return "\n".join(lines)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if args:
        league_id = args[0]
    else:
        from league_config import LEAGUE_ID
        league_id = LEAGUE_ID
    s = summarize(league_id)
    print(json.dumps(s, indent=2) if "--json" in sys.argv else text(s))
    return 0


if __name__ == "__main__":
    sys.exit(main())
