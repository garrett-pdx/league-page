<div align="center">
  <img alt="The Mudd League" src="static/mudd-badge.svg" width="110px" />

# The Mudd League

**[mudd-league.vercel.app](https://mudd-league.vercel.app)**

Standings, matchups, records, trades, rosters, manager bios, keepers and a league
constitution — generated live from the Sleeper API.

</div>

---

## What this is

The league home page for the **Mudd Keeper League**: ten teams, half-PPR, two keepers each,
on Sleeper since 2022. The site displays the league as *The Mudd League*, which is
deliberately not the name Sleeper carries.

It's a fork of **[nmelhado/league-page](https://github.com/nmelhado/league-page)**, an
open-source SvelteKit template by Nicholas Melhado (MIT). Almost everything here is his
work; this repo is the configuration, content and data pipeline for one league on top of
it. If you want the template itself, go upstream — not here.

## Companion project

**[keeper-draft-board](https://github.com/garrett-pdx/keeper-draft-board)**
([live](https://garrett-pdx.github.io/keeper-draft-board/)) is a separate app for running
the keeper draft — keeper cost maths, ADP, the draft board itself. Same league, different
codebase, no shared code. This site links to it; the two are not meant to be merged.

## Running it locally

```bash
npm install       # node_modules is not checked in
npm run dev       # http://localhost:5173
npm run lint      # prettier --check + eslint
```

Node **>= 20**. `npm install` also runs `npm run prepare`, which compiles the Material
theme into `static/smui.css` and `static/smui-dark.css` — both gitignored and regenerated,
so never edit or commit them.

Two build gotchas, neither of our making:

- **`npm run build` fails on Node > 22.** Compilation succeeds and then the Vercel adapter
  rejects the local Node version. It doesn't affect Vercel's own builders. To check a build
  locally, use the node-adapter path: `DOCKER_BUILD=true npx vite build`.
- **`npm run build-docker` is broken upstream** — the script passes `--verbose`, which this
  Vite version rejects outright. Drop the flag if you need the container path.

## Deployment

Vercel, project `mudd-league`. Every push to `master` deploys automatically. No environment
variables are needed: Sleeper's API is public, read-only and unauthenticated. The blog is
off and would need Contentful credentials before it could be turned on.

## The history dataset

`scripts/pull-league-history.py` pulls every season out of Sleeper into six JSON files under
`static/data/` — 1,155 transactions, weekly roster snapshots for all 72 played weeks, player
ownership timelines, keeper chains with cost and lineage, and derived final standings.

```bash
python3 scripts/pull-league-history.py    # ~300 requests, 1-2 minutes
```

Re-run it after a season and commit the diff; nothing in there is hand-edited.
`static/data/README.md` documents every field, including the two traps: roster IDs move
between seasons, and 2022 has two drafts attached to it, only one of which is a 2022 draft.

`weeks.json` is the interesting one — it snapshots every roster, starter and per-player
score for every week, so the league can be reconstructed at any point rather than replayed
from transactions.

## Where to change things

| Want to change | Edit |
| --- | --- |
| League ID, name, homepage text, managers | `src/lib/utils/leagueInfo.js` |
| League rules | `src/routes/constitution/+page.svelte` |
| Manager photos | `static/managers/`, named by Sleeper handle |
| Nav structure | `src/lib/utils/tabs.js` |
| Theme colours | `src/theme/`, then `npm run prepare` |

Prefer configuration over code. This is a fork of an actively maintained project, and every
component edit is a future merge conflict — see `CLAUDE.md` for the fork rules, the data
layer, and the three inherited upstream bugs fixed here.

## Documentation

- `CLAUDE.md` — the league's facts, fork constraints, architecture
- `src/lib/utils/CLAUDE.md` — config and the Sleeper data layer
- `src/routes/CLAUDE.md` — routing and page conventions
- `static/data/README.md` — the dataset
- `docs/blog.md` — the three weekly posts and Contentful setup
- `docs/post-generator-skill.md` — plan for the post-drafting skill

## Credit

Built on [League Page](https://github.com/nmelhado/league-page) by
[Nicholas Melhado](http://www.nmelhado.com/), MIT licensed. If it's useful to you,
[consider donating](https://www.buymeacoffee.com/nmelhado) to the upstream project.
