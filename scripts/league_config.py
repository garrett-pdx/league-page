"""
The league's configuration, for the Python pipeline.

Reads league/league.json -- the same file the site reads -- so the pipeline never hardcodes a
league. Stdlib only, and Python 3.7 compatible, like every script here.

    from league_config import CONFIG, LEAGUE_ID, STAT_CORRECTIONS, ELIGIBILITY

Scripts import this by putting their own directory on sys.path, which `python3 scripts/x.py`
does already.

Three environment variables point a run somewhere else, so the pipeline can be tested against any
league without touching this one's committed files:

    LEAGUE_CONFIG   path to a league.json            (default: league/league.json)
    LEAGUE_DATA     directory for the dataset        (default: static/data)
    LEAGUE_DOCS     directory for generated docs     (default: docs)
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.environ.get("LEAGUE_CONFIG") or os.path.join(ROOT, "league", "league.json")
DATA_DIR = os.environ.get("LEAGUE_DATA") or os.path.join(ROOT, "static", "data")
DOCS_DIR = os.environ.get("LEAGUE_DOCS") or os.path.join(ROOT, "docs")

with open(CONFIG_PATH) as f:
    CONFIG = json.load(f)

LEAGUE_ID = CONFIG["sleeperLeagueId"]
LEAGUE_NAME = CONFIG["name"]
SITE_URL = (CONFIG.get("siteUrl") or "").rstrip("/")

# Strict: every disagreement with Sleeper's own settled figures (a record a game off, a season's
# potential points a few points out) fails the pipeline instead of being reported as a warning.
# A league that has pinned every quirk in overrides can afford it; a new one usually cannot.
STRICT = bool((CONFIG.get("pipeline") or {}).get("strict"))

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

# The league's keeper-cost rule (league.json keepers.rule), or None. With one, keepers.json says
# what each keeper should have cost and whether it did; without one it records the facts only.
KEEPER_RULE = (CONFIG.get("keepers") or {}).get("rule")

# Seasons played before Sleeper, and the Sleeper draft IDs of any drafts imported from them.
PRE_SLEEPER = sorted(
    ((CONFIG.get("history") or {}).get("preSleeper") or []), key=lambda s: s["season"]
)
IMPORTED_DRAFT_IDS = {s["importedDraftId"]: s["season"] for s in PRE_SLEEPER if s.get("importedDraftId")}
