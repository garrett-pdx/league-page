# Plan: open-sourcing the site as a Sleeper league template

Started 2026-10-04 on the `open-source` branch. This is the roadmap for turning the Mudd League
site into a template that anyone, or any coding agent, can point at a Sleeper league and get the
same site: live standings and matchups, a full history archive, records, Stat Lab, lore, manager
pages, a constitution and an AI-written weekly blog.

Read this before working on the branch. Update the checklists as work lands.

## Decisions (Garrett, 2026-10-04)

1. **Refactor here, then split.** The generalization happens on the `open-source` branch of this
   repo, with the Mudd League as the first league on it, so muddleague.site is the regression
   test for every step. When the engine is done, a new public template repo is created from the
   branch with a neutral demo league in place of Mudd's. Mudd keeps deploying from this repo.
   `master` only receives the branch once the Mudd site renders the same on it.
2. **Hard fork with a new name.** The project gets its own name and versioning and credits
   [nmelhado/league-page](https://github.com/nmelhado/league-page) under its MIT licence (keep
   Nicholas Melhado's copyright line; add ours below it). The "keep `git merge upstream/master`
   boring" rule in the root `CLAUDE.md` no longer binds engine files: restructure freely. The
   update checker (`src/lib/version.js`) gets pointed at the new project's releases.
   **Name (Garrett, 2026-10-04): Fantasy Football Website with History**, repository and package
   `fantasy-football-website-with-history` (free on npm; no repository of that name exists).
3. **The blog runs on markdown in the repo by default.** Posts are `.md` files under
   `league/posts/`; an agent writes one and commits it, and the deploy publishes it. No
   Contentful account, no tokens. Contentful stays as an optional backend, so Mudd can keep it.
4. **The template ships a neutral demo league.** Placeholder names, no real bios, photos or
   hometowns. The README links muddleague.site as the live example.

## The contract: engine and league

Everything about one league lives in **`league/`**. Everything else is the engine, which no
league edits. Updating a site to a new engine release then never conflicts with its content.

```
league/                    HAND-AUTHORED, one league's content (the only thing a league edits)
  league.json              identity, features, theme, links, history quirks, data overrides,
                           managers; validated against schema/league.schema.json
  home.md                  the homepage intro (markdown; raw HTML allowed)
  constitution.md          the rules; ## sections and ### numbered rules become the TOC
  voice.md                 the blog's house style, read by the recap and preview skills
  posts/                   blog posts (markdown backend)
  managers/                manager photos, referenced from league.json by file name
  archive-facts.json       the Trophy Room's "From the archives" facts
  NOTES.md                 league-specific facts for agents (what the root CLAUDE.md holds today)

static/data/, static/brand/, favicons, manifest
                           GENERATED from league/ and Sleeper. Committed, never hand-edited.

schema/league.schema.json  the config's contract, with a description on every field
```

**Rule for agents:** a league's content changes touch `league/` only. When a league needs
something the engine cannot express, add a config option to the engine; never special-case a
league inside a component.

### Config shape (draft, firm up in Phase 1)

```jsonc
{
  "$schema": "../schema/league.schema.json",
  "sleeperLeagueId": "1312235880743706624",   // current season; history walks previous_league_id
  "name": "The Mudd League",                  // display name; may differ from Sleeper's
  "shortName": "Mudd League",                 // PWA name, tight spaces
  "siteUrl": "https://muddleague.site",
  "founded": 2021,                            // may predate the Sleeper record
  "theme": { "primary": "#...", "accent": "#...", "emblem": "#..." },
  "blog": { "backend": "markdown|contentful|none", "title": "The Mudd Report", "intro": "...",
            "contentful": { "postType": "blogPost", "commentType": "blogComment" },
            "comments": false },
  "links": [ { "name": "...", "url": "...", "description": "...", "nav": true } ],
  "history": {
    "preSleeper": [ { "season": 2021, "platform": "ESPN", "importedDraftId": "...",
                      "summary": "..." } ]
  },
  "overrides": {                               // pipeline corrections, each with a note
    "statCorrections": [ { "season": 2023, "userId": "...", "pf": -2.0, "note": "..." } ],
    "eligibility": [ { "season": 2022, "playerId": "4381", "positions": ["TE"], "note": "..." } ]
  },
  "managers": [ { "userId": "...", "name": "...", "location": "...", "photo": "gurret.jpg",
                  "bio": "...", "rival": { "userId": "..." } } ]
}
```

Changes from today's `leagueInfo.js` worth having anyway:

- **`rival` references a `userId`, not an array index**, so reordering managers can no longer
  silently re-pair rivals. Name and photo come from the rival's own entry.
- **`dynasty` stays a config flag** (it is read synchronously by the news feeds and Resources),
  but the setup skill sets it from Sleeper's `settings.type` (0 redraft, 1 keeper, 2 dynasty).
- **Never-rostered users are derived** (`neverRostered` on `getLeagueTeamManagers()`: anyone in a
  season's user list who never owned or co-owned a roster), replacing the `Football_Team` ID
  hardcoded in three components. The root `CLAUDE.md` claimed `league-history.json` carries
  `users_without_roster`; it does not.
- **Page intros are configurable** (`pages.<key>.intro`): they are the league's voice, and several
  held Mudd facts ("since 2022", "Ten managers"). The engine defaults hold none.
- JSON, not JS, so the Python pipeline (stdlib only, runs on Python 3.7) reads the same file.
  Prose that needs markup lives in the markdown files.

## Phases

### Phase 0: plan and branch

- [x] `open-source` branch created from `f2c60a3`.
- [x] This document.

### Phase 1: extract Mudd into `league/` (site renders identically)

- [x] `league/league.json` and `schema/league.schema.json`; `src/lib/utils/leagueInfo.js` is now
      a loader that keeps its old exports (plus new ones); `scripts/league_config.py` for the
      pipeline. `$league` alias (svelte.config.js) and `league` on Vite's `server.fs.allow`.
- [x] Pipeline reads the league ID, stat corrections and eligibility from config
      (`pull-league-history.py`, `derive-site-data.py`, `week-facts.py`); `derive-site-data`
      output byte-identical apart from its date stamp.
- [x] Hardcoded strings to config: the app name (`app.html` metas moved to `+layout.svelte`;
      `manifest.json` is now a prerendered route), the blog's name and intro, the league links
      and nav tools (`LeagueLinks`, `tabs.js`), `siteUrl` and the series prefix
      (`publish-article.mjs`). The seal waits for Phase 3.
- [x] Pre-Sleeper seasons generalized: `FOUNDING_SEASON`, `CARRIED_OVER_DRAFT_ID` and
      `EspnSeason.svelte` (now `PreSleeperSeason.svelte`) driven by `history.preSleeper`.
- [x] Never-rostered users derived (`ManagerSelectors`, `Lab`, `HeadToHeadGrid`).
- [x] `homepageText` from `league/home.md`; constitution from `league/constitution.md`, rendered
      by `parseConstitution()` in `src/lib/utils/markdown.js` (`marked`). Expanded text is
      identical to the old hand-coded page.
- [x] Manager photos in `league/managers/` (bundled through `import.meta.glob`), rivals by `userId`.
- [x] `archiveFacts.js` to `league/archive-facts.json`.
- [x] Page intros configurable (`pages`).
- [x] Before/after check of every page against the snapshots taken at the start of the phase.
- [x] Remaining Mudd strings in code comments and the nested `CLAUDE.md` files (Phase 5).

### Phase 2: generalize the data pipeline and the pages for any Sleeper league

The pipeline's self-checks are the safety net: they fail the run on any league the code does
not understand. That is correct behaviour, and it means today they fail on most leagues.

| Format | Pipeline | Pages | Notes |
| --- | --- | --- | --- |
| Slots: QB RB WR TE FLEX | yes | yes | today's only supported shape |
| K, DEF | no | ? | solver ignores them |
| SUPER_FLEX, WRRB_FLEX, REC_FLEX | no | partial | `FLEX_OK` is hardcoded RB/WR/TE |
| IDP: DL LB DB IDP_FLEX | no | ? | |
| Median game (`league_average_match`) | no | no | records check will fail |
| Divisions | n/a | removed | Standings dropped the column |
| Ties | ? | removed | |
| Playoff size 2/4/6/8, byes | ? | ? | |
| Keeper / dynasty / redraft | keeper | keeper | keeper pages must hide for redraft |
| Best ball (`best_ball`) | ? | ? | efficiency is always 100%; hide it |
| First season (no history) | ? | ? | every history page needs an empty state |
| Taxi squad, co-owners, orphaned rosters | ? | ? | |
| Team count other than 10 | `or 10` default | ? | |

- [x] One lineup solver (`scripts/lineup.py`), shared by `derive-site-data.py` and
      `week-facts.py`: every Sleeper slot type, Sleeper's greedy for the potential-points check,
      an exact assignment for the true optimum. Eligibility from `fantasy_positions` plus what
      each season's lineups prove.
- [x] Median games: records, standings, season tables, points per game.
- [x] Divisions and ties in Standings when the league has them; division-first seeding.
- [x] Playoffs of any size, two-week rounds, consolation brackets and toilet bowls, byes,
      exhibition fixtures; final standings and season brackets for all of them.
- [x] Orphaned rosters (stand-in managers), stat corrections detected by pairing, and
      disagreements with Sleeper as warnings unless `pipeline.strict`.
- [x] Keeper-cost rule as config (`keepers.rule`); without one, facts only.
- [x] Empty states for a first-season league (tested on a real one) and empty derived files when
      no week is complete.
- [x] Best ball: Lineup IQ hidden when every lineup is perfect.
- [x] **Test matrix**: 13 public leagues from upstream's forks covering every format above, plus
      a first-season league. All run the whole pipeline; 486 of 518 manager-seasons reproduce
      Sleeper's potential points to the cent. `scripts/try-league.sh` and
      `npm run dev:league` make any league testable without touching this one.
- [ ] Free agents covers QB/RB/WR/TE only; kickers, defenses and IDP are not searched yet.
- [ ] Imported drafts are confirmed with the commissioner by the setup skill rather than
      detected automatically.
- [ ] One 16-team, 8-seed league seeds in an order no standard rule reproduces; left approximate.

### Phase 3: brand generator

- [x] `npm run brand` (`scripts/brand.mjs`): theme colours to a contrast-checked token file
      (`src/theme/_league.scss`), brand art from `scripts/brand-templates/` (name, tagline and
      year sized to fit), icons; `league/brand/` overrides any file. Tokens renamed by role
      (`--brand*`, `--trophy*`, `--emblem`). Mudd's palette and art reproduce byte for byte.
- [ ] Per-league brand in `npm run dev:league` previews (today the preview shows the main
      league's brand).

### Phase 4: markdown blog

- [x] `league/posts/*.md` with `key: value` frontmatter, rendered with `marked` in the shape the
      Contentful backend returns; `blog.backend` switch; `publish-article.mjs` writes markdown
      posts; the home card hides itself when there are no posts.

### Phase 5: agent layer

- [x] Root `CLAUDE.md` is the engine's guide; the league's facts moved to `league/NOTES.md`;
      nested `CLAUDE.md` files genericized; `AGENTS.md` points other agents at them.
- [x] Skills: `league-setup` (league ID to deployed site), `league-data`, `league-recap`,
      `league-preview`, `league-season`. The `mudd-*` skills are replaced: Mudd's voice and
      publishing details are in `league/voice.md`, the shared craft in `docs/writing.md`, and
      post drafts moved to `league/drafts/`.
- [x] Tools the skills use: `league-summary.py`, `sync-managers.py`, `suggest-rivals.py`,
      `find-current-league.py`; `projections.py` and `repeat-check.py` made league-neutral.
- [x] Opt-in `refresh-data` GitHub Action (runs only with the repository variable
      `REFRESH_DATA` set to true).

### Phase 6: split and publish

- [ ] Demo league config, README, `docs/setup.md` (the skills already point to it), licence
      credit, package.json metadata, version checker, CHANGELOG reset.
- [ ] New public repo created from the branch with the demo `league/`; Mudd's `league/` stays here.
- [ ] Mudd-only material stays in this repo: `docs/articles/`, `mudd-voice.md` (becomes
      `league/voice.md`), the revamp log and plan docs, one-off scripts.

## Verification

Phase 1 is a pure refactor. Before any change, every page was captured as text from the dev
server (`scratchpad/before/`); each step is checked against those captures, allowing for live
Sleeper data that moves on its own (scores, transactions, the NFL week).

## Open questions

- Whether Mudd moves its existing posts from Contentful to markdown (a migration script is
  cheap once Phase 4 lands).
