---
name: league-season
description: The league site's season rollover — the end-of-season wrap once the title game is final (final standings, champion, records, bios, Trophy Room facts) and the preseason refresh (Sleeper's new league ID for the new season, links that go stale, keepers and the draft). Use when the championship is decided, when asked to "close out the season", "update the site for the new season", "Sleeper renewed the league", "the draft is done", or when the site still shows last season after a renewal.
---

# Season rollover

Two moments a year when the hand-written parts of the site go stale. Everything generated from
data refreshes itself through the pipeline; this is everything that doesn't.

## End of season (after the title game is final)

1. **Refresh the data** (`league-data` skill): `python3 scripts/pull-league-history.py`, then
   `npm run derive-site-data`, then `npm run derive-narratives`. Every self-check must pass.
   The finished season now has `final_standings` in `league-history.json`; if not, the bracket
   isn't complete in Sleeper yet. Commit `static/data/` and `docs/league-lore.md` together.
2. **Check the season's page** (`/seasons/<year>`): final table, bracket, champion, title game.
   And the Trophy Room and the home page's champion panel (both update themselves).
3. **Update the hand-written lines.** Bios in `league/league.json` that say "reigning champion"
   or scope a figure to a range of seasons; `league/voice.md`'s career figures; any season
   scoping in `league/NOTES.md`. Re-derive every number from the data; never edit from memory.
4. **Refresh the Trophy Room facts** in `league/archive-facts.json`: recompute every figure,
   move any "through <year>" scope on to the season just finished, and replace a fact the season
   has broken.
5. **Pipeline warnings for the new season**: if `derive-site-data` reported disagreements,
   either pin them in `league.json` overrides (each warning prints the entry) or note why in
   `league/NOTES.md`.

## Preseason (once Sleeper renews the league)

1. **The new league ID.** Sleeper gives a renewed league a new ID; the site keeps showing last
   season until `sleeperLeagueId` changes:
   ```bash
   python3 scripts/find-current-league.py           # report
   python3 scripts/find-current-league.py --write   # update league.json
   ```
2. **Re-run the pipeline**; the new season appears once it has a completed week, and the
   preseason pages fall back to last season until then.
3. **Rules that changed** (roster spots, scoring, playoffs): `python3 scripts/league-summary.py`
   shows the new settings; update `league/constitution.md` with what the league voted, and only
   that.
4. **Links that go stale**: anything in `links` with a year in its URL; check every external
   link still answers.
5. **New or departed managers**: `python3 scripts/sync-managers.py --photos` adds newcomers;
   departed managers stay in `managers` and move to the Moratorium on their own. Re-run
   `python3 scripts/suggest-rivals.py` if pairings broke.
6. **After the draft**: re-run the pipeline so the draft and keepers reach the dataset, and check
   `/drafts` and the season page's keepers.
