# Changelog

Engine releases. `python3 scripts/update-engine.py` brings a site up to date; anything that needs
a step from you after updating is called out under its version.

## 1.0.1

- **Launch screens in your league's look.** The iOS launch screens (`static/pwa/apple-splash-*`)
  were League Page's; `npm run brand` now renders them from your seal and wordmark, one per size
  `src/app.html` declares.
- `update-engine.py` treats everything in `static/pwa/` as your league's, and reads that rule from
  the new release, so a generated file a release adds is safe from the first update. It refuses
  to run outside a git repository, and `--from` copies tracked files only.
- Generic data-format guide in `docs/data.md`; setup docs say to replace the whole demo league.

**After updating from 1.0.0:** run `npm run brand`. 1.0.0's updater copies the template's launch
screens over yours; this renders your own.

## 1.0.0

The first release, grown out of [League Page](https://github.com/nmelhado/league-page) 2.5.1 and
the Mudd League's site.

- **One directory per league.** Everything about a league is in `league/`: `league.json`
  (validated by `schema/league.schema.json`), `home.md`, `constitution.md`, `voice.md`,
  `NOTES.md`, photos, brand overrides and blog posts. The engine holds nothing league-specific.
- **A history archive built from Sleeper**: every season's final table, bracket, title run, draft,
  keepers, trades and extremes; records; Stat Lab; the Trophy Room and Hall of Fame; rivalries;
  manager careers; generated lore. The data pipeline (`scripts/`) handles any Sleeper format and
  checks itself against Sleeper's records before writing.
- **Any format**: every lineup slot (superflex, IDP, kickers, defenses, every flex), median games,
  divisions, ties, playoffs of any size with byes and two-week rounds, consolation brackets and
  toilet bowls, orphaned rosters, seasons played before Sleeper, first-season leagues.
- **Generated brand**: `npm run brand` turns two colours into a contrast-checked palette, a seal,
  a wordmark, a ribbon, a laurel and every icon.
- **A Markdown blog** (the default; Contentful still supported) and agent skills that write and
  fact-check a weekly recap and preview.
- **Agent playbooks** in `.claude/skills/`: `league-setup`, `league-data`, `league-recap`,
  `league-preview`, `league-season`.
- **Tools**: `try-league.sh` and `npm run dev:league` (try any league without touching yours),
  `league-summary.py`, `sync-managers.py`, `suggest-rivals.py`, `find-current-league.py`,
  `update-engine.py`, and an opt-in GitHub Action that refreshes the data twice a week.

League Page's own history is at
[nmelhado/league-page](https://github.com/nmelhado/league-page/blob/master/CHANGELOG.md).
