<div align="center">
  <img alt="The Mudd League" src="static/brand/wordmark.svg" width="320px" />

# The Mudd League

**[muddleague.site](https://muddleague.site)** (also at mudd-league.vercel.app)

Standings, matchups, records, trades, rosters, manager bios, keepers and a league
constitution — generated live from the Sleeper API.

</div>

---

## What this is

The league home page for the **Mudd Keeper League**: ten teams, half-PPR, two keepers each,
on Sleeper since 2022. The site displays the league as *The Mudd League*, which is
deliberately not the name Sleeper carries.

It runs on **[Fantasy Football Website with History](https://github.com/garrett-pdx/fantasy-football-website-with-history)**,
the open-source template that grew out of this repository (itself a fork of Nicholas
Melhado's [League Page](https://github.com/nmelhado/league-page)). Everything about this
league is in `league/`; everything else is that engine, and `python3 scripts/update-engine.py`
brings in new releases. If you want a site for your own league, start from the template, not
from here.

## Companion project

**[keeper-draft-board](https://github.com/garrett-pdx/keeper-draft-board)**
([live](https://garrett-pdx.github.io/keeper-draft-board/)) is a separate app for running
the keeper draft — keeper cost maths, ADP, the draft board itself. Same league, different
codebase, no shared code. This site links to it; the two are not meant to be merged.

## Running it locally

```bash
npm install       # node_modules is not checked in
npm run dev       # http://localhost:5173
```

The engine's commands, gotchas and architecture are in `CLAUDE.md`; setup from scratch is
`docs/setup.md`.

## Deployment

Vercel, project `mudd-league`. Every push to `master` deploys automatically. The blog (The
Mudd Report) reads Contentful with the read-only delivery token, set in Vercel.

## Where to change things

| Want to change | Edit |
| --- | --- |
| League ID, name, links, managers, theme, history | `league/league.json` |
| Home page copy | `league/home.md` |
| League rules | `league/constitution.md` |
| Manager photos | `league/managers/`, named by Sleeper handle |
| The blog's voice and publishing details | `league/voice.md` |
| Colours or logo | `theme` in `league.json` (or `league/brand/`), then `npm run brand` |

## Documentation

- `CLAUDE.md` — the engine: architecture, data pipeline, design system
- `league/NOTES.md` — this league's facts, decisions and quirks
- `.claude/skills/` — the weekly blog, data refresh, season rollover and setup playbooks
- `docs/data.md` — the dataset
- `docs/plan-open-source.md` — how this site became the template

## Credit

Built with [Fantasy Football Website with History](https://github.com/garrett-pdx/fantasy-football-website-with-history),
which began as a fork of [League Page](https://github.com/nmelhado/league-page) by
[Nicholas Melhado](http://www.nmelhado.com/). MIT licensed. If League Page is useful to you,
[consider donating](https://www.buymeacoffee.com/nmelhado) to it.
