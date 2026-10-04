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
   **The name is still open** (see "Open questions").
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
- [ ] Before/after check of every page against the snapshots taken at the start of the phase.
- [ ] Remaining Mudd strings in comments and docs (`leagueAwards.js`, `statLab.js`, theme files,
      `src/lib/utils/CLAUDE.md`, `src/routes/CLAUDE.md`) are cleaned up in Phase 5.

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

- [ ] One lineup solver, shared by `derive-site-data.py` and `week-facts.py`, that handles every
      Sleeper slot type, keeps reproducing `potential_points` to the cent, and names the player
      and week when it cannot (so the fix is an `eligibility` override, not a code change).
- [ ] Median games: records, all-play, schedule luck and standings.
- [ ] Divisions and ties back in Standings when the league has them.
- [ ] Keeper UI (badges, keeper pages, keeper chains) only when the league keeps players.
- [ ] **Keeper cost rule is Mudd's, hardcoded** in `build_keepers()` (`pull-league-history.py`)
      and in the notes `Keepers.svelte` writes: cost = last season's round, one round dearer when
      the same manager keeps again, undrafted costs the last round. Other leagues price keepers
      differently (a fixed round penalty, auction value, no cost). Make it a `keepers.costRule`
      in `league.json`, and compute `expected_cost_round` / `matches_rule` only when one is set.
- [ ] Empty states for a first-season league and a fresh install before the first pull.
- [ ] Imported drafts detected and offered to the setup skill as `history.preSleeper` candidates.
- [ ] **Test matrix of real public leagues.** Upstream has ~1,300 forks, each with a league ID in
      `leagueInfo.js`; pick ones covering every row above and run pull + derive + self-checks on
      each. Keep their data out of the repo (scratch directory); commit only small synthetic
      fixtures if a test needs one.

### Phase 3: brand generator

- [ ] `league.json` theme (two or three colours) produces the design tokens; contrast checked
      (body ink AA, never gold-as-ink), with ink shades derived when a colour fails.
- [ ] Seal and wordmark SVGs generated from name, ring text and founding year; the existing
      Mudd art becomes the output for Mudd's inputs (or stays as a hand-made override).
- [ ] `render-icons.js` driven by the generated seal; `manifest.json` generated from config.

### Phase 4: markdown blog

- [ ] `league/posts/*.md` with simple `key: value` frontmatter (title, date, type, author,
      featured, summary) rendered with `marked`; same `/blog` and `/blog/<slug>` pages.
- [ ] `blog.backend` switch; Contentful kept behind it.
- [ ] `publish-article.mjs` writes to `league/posts/` for the markdown backend.

### Phase 5: agent layer

- [ ] Engine `CLAUDE.md` (architecture, conventions, design system, Sleeper data traps: the
      week 18 phantom, unplayed seasons, keepers in draft slots, roster IDs moving) and
      `league/NOTES.md` (one league's facts). Today's root `CLAUDE.md` splits between the two.
- [ ] **`league-setup` skill**: league ID in, then: read Sleeper (format, history, managers,
      imported drafts), interview the commissioner (name, colours, voice, bios), write
      `league.json`, run the pipeline, generate the brand, draft a constitution from the Sleeper
      settings, deploy to Vercel.
- [ ] Generic `league-data`, `league-recap`, `league-preview` skills (from `mudd-*`), reading
      `league/voice.md`. Mudd's skills become thin wrappers or are replaced.
- [ ] `league-season` skill for the end-of-season and preseason checklists.
- [ ] `derive-narratives` and `league-lore.md` produced for any league.

### Phase 6: split and publish

- [ ] Demo league config, README, setup guide, config reference, licence credit, package.json
      metadata, version checker, CHANGELOG reset.
- [ ] New public repo created from the branch with the demo `league/`; Mudd's `league/` stays here.
- [ ] Mudd-only material stays in this repo: `docs/articles/`, `mudd-voice.md` (becomes
      `league/voice.md`), the revamp log and plan docs, one-off scripts.

## Verification

Phase 1 is a pure refactor. Before any change, every page was captured as text from the dev
server (`scratchpad/before/`); each step is checked against those captures, allowing for live
Sleeper data that moves on its own (scores, transactions, the NFL week).

## Open questions

- **Project name.** Needed by Phase 6 (package.json, README, repo name, update checker).
- Whether Mudd moves its existing posts from Contentful to markdown (a migration script is
  cheap once Phase 4 lands).
