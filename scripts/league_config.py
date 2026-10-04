"""
The league's configuration, for the Python pipeline.

Reads league/league.json -- the same file the site reads -- so the pipeline never hardcodes a
league. Stdlib only, and Python 3.7 compatible, like every script here.

    from league_config import CONFIG, LEAGUE_ID, STAT_CORRECTIONS, ELIGIBILITY

Scripts import this by putting their own directory on sys.path, which `python3 scripts/x.py`
does already.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT, "league", "league.json")

with open(CONFIG_PATH) as f:
    CONFIG = json.load(f)

LEAGUE_ID = CONFIG["sleeperLeagueId"]
LEAGUE_NAME = CONFIG["name"]
SITE_URL = (CONFIG.get("siteUrl") or "").rstrip("/")

_overrides = CONFIG.get("overrides") or {}

# (season, user_id) -> {"pf": x, "pa": y}: the exact difference between a manager-season's
# weekly sum and Sleeper's settled season figure, where a stat correction came after settlement.
STAT_CORRECTIONS = {}
for _c in _overrides.get("statCorrections") or []:
    _key = (str(_c["season"]), str(_c["userId"]))
    _entry = STAT_CORRECTIONS.setdefault(_key, {})
    for _field in ("pf", "pa"):
        if _field in _c:
            _entry[_field] = _entry.get(_field, 0.0) + float(_c[_field])

# (season, player_id) -> set of positions Sleeper actually allowed that season.
ELIGIBILITY = {
    (str(_e["season"]), str(_e["playerId"])): set(_e["positions"])
    for _e in _overrides.get("eligibility") or []
}

# Seasons played before Sleeper, and the Sleeper draft IDs of any drafts imported from them.
PRE_SLEEPER = sorted(
    ((CONFIG.get("history") or {}).get("preSleeper") or []), key=lambda s: s["season"]
)
IMPORTED_DRAFT_IDS = {s["importedDraftId"]: s["season"] for s in PRE_SLEEPER if s.get("importedDraftId")}
