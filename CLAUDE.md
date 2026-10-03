# CLAUDE.md — Mudd Keeper League Page

Context and conventions for this repo. Read this first.

## What this is

The **league home page** for the Mudd Keeper League — a public, always-on site with
standings, matchups, records, trades, rosters, manager bios, and a league constitution,
all generated live from the Sleeper API.

It is a **fork of [nmelhado/league-page](https://github.com/nmelhado/league-page)** (an
open-source SvelteKit template, currently v2.5.1), not a project written from scratch.
`origin` is `https://github.com/garrett-pdx/league-page.git`, default branch `master`.
That fork relationship is the single most important fact about working here — see
"Working in a fork" below.

**Status: live at [muddleague.site](https://muddleague.site)** (bought through Vercel, which runs
its DNS; `mudd-league.vercel.app` serves the same site, so old links still work). Every push to
`master` deploys. `leagueInfo.js` is fully configured; all eleven managers (ten active plus
Jordan Leonard in the Moratorium) have real names, hometowns, locally-served photos and
bios; the constitution is this league's rules; the shell is rebranded.

Still outstanding, in rough priority order:

- **The blog is on, comments are not.** `enableBlog = true`, against a real Contentful
  space, using only the read-only delivery token. `enableComments = false` is ours: the
  league doesn't want comments, and the management token that writing them would require is
  the one genuinely dangerous variable under Vite's browser-exposing `VITE_` prefix, so it
  is deliberately unset. See `src/lib/utils/CLAUDE.md` before re-enabling.
  Two weekly posts are live, each written by a project skill: `mudd-monday` (the Monday
  recap) and `mudd-preview` (the midweek preview), both built on `mudd-data`
  (`scripts/week-facts.py`), with the house style in `docs/mudd-voice.md` and publishing via
  `scripts/publish-article.mjs`. Titles end in `RECAP` / `PREVIEW` because the publisher
  matches on title. `--type` becomes the post's category on /blog (the filter is built from
  the posts' own `type` values, and Contentful's field has no allowed-values list): Monday
  posts are `Recap`, previews `Preview`. The week 2–4 previews went out as `Recap` and still
  need retagging in Contentful.
- **The home page copy was approved by Garrett on 2026-10-03.** `homepageText` was rewritten
  in the 2026-10 revamp: a shorter intro, a "Find your way" row, the rules reduced to one line
  pointing at the constitution, and no hand-kept champion paragraph.
- **`static/data/` is fetched at runtime by three helpers, and only for five files.** All three
  memoize per session, take SvelteKit's `fetch` so they work during SSR, and never cache a
  failed fetch. Sizes are raw / gzipped:
  - `helperFunctions/leagueHistory.js` → `league-history.json` (131 KB / 11 KB), for the
    manager career band, the Hall of Fame, Standings, Stat Lab and Seasons. It is the only
    source for a full 1–10 finish — Sleeper exposes podium and toilet bowl only — and it keys
    on `user_id`, which sidesteps roster IDs moving between seasons.
  - `helperFunctions/leagueGames.js` → `games.json` (26 KB / 6 KB), for schedule luck on
    Standings, the head-to-head grid on Rivalry, Seasons and Stat Lab. It also holds the pure
    `filterGames` / `allPlay` / `headToHead` / `standingsFrom` / `liveSeasonGames` /
    `benchPoints` / `lineupEfficiency` / `lineupTotals` those pages compute with.
  - `helperFunctions/seasonNotes.js` → `season-notes.json` (24 KB / 4 KB) for `/seasons` and
    each year page, plus `keepers.json` (32 KB / 2 KB) and `players.json` (20 KB / 6 KB) for
    the year pages only.

  `games.json` and `season-notes.json` are built by `npm run derive-site-data`; the other three
  come straight from the pull. **Nothing else in `static/data/` is fetched at runtime** — not
  `weeks.json` (372 KB), `transactions.json` (322 KB) or `narratives.json` (102 KB). Anything new
  that wants one of those needs a derived, size-budgeted file instead, as `games.json` is for
  `weeks.json`.
- **`weeks.json` is mined offline instead.** `npm run derive-narratives` reads it (plus the draft,
  keeper and transaction files) and writes `static/data/narratives.json` and `docs/league-lore.md`
  — 294 facts across 25 categories, each with structured fields *and* a plain-English `text`.
  It is an authoring aid for recaps, bios and homepage copy; nothing in `src/` fetches it and
  nothing should without a size budget. **Three definitions changed in the 2026-10 lore fix**,
  and any figure quoted from before it may be wrong: a player's value to a manager (MVPs,
  keepers, draft steals, FAAB) counts **starter points only**, never bench points; points left
  on the bench are the best legal lineup minus the score, **reproducing Sleeper's
  `potential_points` to the cent** for all 50 manager-seasons; and game scores are
  **official**, so the commissioner override beats the computed score. The file carries its
  own `definitions` array; `static/data/README.md` has the override, `STAT_CORRECTIONS` and
  eligibility details. Bench facts still can't tell an IR stash from a benching, so check
  before a post mocks anyone for one. Three traps it encodes, all of which produced wrong facts
  first time round: **every season carries a week 18 with `matchup_id: 0`** and no lineups set
  (median score ~55 against ~100), which must be excluded or it invents a playoff round;
  **keepers occupy draft slots**, so draft "steals" and "busts" have to filter `is_keeper` or
  they retell keeper decisions as draft ones; and **a scheduled-but-unplayed season looks
  completely real** — once Sleeper publishes the schedule, every week returns ten rosters, eight
  starters each and genuine non-zero `matchup_id`s, with every score `0.0`. Testing
  `if WEEKS[season]` passes it straight through, so on 2026-09-08 (a day before kickoff) the
  unplayed 2026 season swept every worst-of derivation and crashed the script outright when
  twenty keepers tied at `(0.0, "2026")` and the sort fell through to comparing dicts.
  `season_played()` now requires a point to have been scored somewhere. Note the puller is
  already correct here — `final_standings` holds completed seasons only, which is why the live
  site never saw a phantom 2026 table. The pull itself now goes further and writes completed
  weeks only (see "The data pipeline").
- **Sortable record tables were considered and rejected for the six *record* tables.** Each is
  a top-N list defined by its own metric, and the rank column is positional (`{ix + 1}`), so
  re-sorting renumbers rank into nonsense. The four *ranking* tables (Win %, Points, Lineup IQ,
  Transactions) are sortable by column (`sortRanking` in `RecordsAndRankings.svelte`). For
  anything more, **Stat Lab (`/stat-lab`) is the sortable view**: games, seasons and careers,
  13 measures, every column sortable, rank recomputed after each sort, and the whole view held
  in the address so it can be linked.
- **Optional manager fields are unset** — `favoriteTeam`, `preferredContact`,
  `fantasyStart`, `philosophy`, `tradingScale`, `favoritePlayer`, `valuePosition`. Each is
  `{#if}`-guarded and simply **hidden** when unset, so for now a manager page's fantasy-info row
  holds only the Rival tile. The managers have been asked for them (`docs/site-todo.md`).
- **Rivals are real pairings.** Each of the ten active managers has one rival and none is
  shared: five pairs, a maximum-weight matching over head-to-head history (frequency,
  closeness, stakes). The method is in the comment above `managers` in `leagueInfo.js`.
  `rival.link` is an *index* into the array, so don't reorder it. Jordan Leonard's rival is
  "The Field" (`link: null`, which goes to the directory). The Rival tile links to the rival's
  page, with a separate Head-to-head link under it.

**The league is displayed as "The Mudd League."** Sleeper names it "Mudd Keeper League";
`leagueName` deliberately differs from the Sleeper-side name. Don't "correct" it to match
the API.

## Companion project (different repo, different purpose)

`~/Desktop/ff_keeper` → [garrett-pdx/keeper-draft-board](https://github.com/garrett-pdx/keeper-draft-board),
live at <https://garrett-pdx.github.io/keeper-draft-board/>. A separate Vite/TypeScript
static app for running the league's **keeper draft** (roster browsing, keeper cost math,
draft board). It has its own detailed `CLAUDE.md` — read that one, not this one, for
keeper-cost rules, ADP/value pipelines, or the shared-keeper Gist.

The two projects **share a league, not a codebase**. Don't copy code between them; don't
try to unify them. This site links to the board from `tabs.js` (League → Rules & Tools), from
`homepageText`, and from `src/lib/Resources/LeagueLinks.svelte`.

On keeper rules the two now disagree in one place, deliberately. **The constitution is the
source of truth for what the league does**; the board's `CLAUDE.md` remains the reference
for how the board computes things. See the collision note below before "fixing" either.

## The league (facts, verified against the Sleeper API 2026-08-09)

- **Mudd Keeper League**, 10 teams. Keeper league — **not dynasty** (`dynasty = false` in
  `leagueInfo.js`; the template's default is `true`). **Founded in 2021 on ESPN**, moved to
  **Sleeper for 2022**. Only the 2021 draft came across in the move (see the history-dataset
  notes below), so 2022 is the start of the *record*, not the start of the league — this is
  what the otherwise-mysterious second 2022 draft in `league-history.json` actually is.
  The founding year is stated on the seal (`static/brand/seal.svg`) and in the homepage and
  constitution copy; keep all four in step.
- The name traces to **Claremont-Mudd-Scripps**, where at least some of the managers played
  college football together — useful for the tone of homepage/constitution copy, and the
  reason the site displays "The Mudd League" rather than Sleeper's "Mudd Keeper League".
- Sleeper league IDs, newest first. League Page only needs the **current** one and walks
  `previous_league_id` backwards itself:
  | Season | League ID |
  | --- | --- |
  | 2026 (current) | `1312235880743706624` |
  | 2025 | `1257452519521517570` |
  | 2024 | `1124503476031041536` |
  | 2023 | `982140218121711616` |
  | 2022 (first) | `819042960179077120` |
- Scoring **0.5 PPR**, 6-point passing TDs. Starters: QB, RB, RB, WR, WR, TE, FLEX, FLEX,
  5 bench, 2 IR (6 bench through 2025; the league voted 7–3 to cut it, and the draft from 14
  rounds to 13, for 2026). Playoffs: 4 teams, starting week 16. Waivers: FAAB, $100 budget.
  Trade deadline week 12.
- Keepers: **2 per team** (`max_keepers` on the Sleeper league). The full rule set —
  cost = the round the player was drafted last year, +1 round of inflation when the *same
  manager* keeps him again, undrafted players cost the final round — lives in the draft
  board's `CLAUDE.md`. **League Page has no built-in keeper concept** — `dynasty` is a
  cosmetic content flag, not a league type. We added the one exception ourselves: the
  drafts page reads Sleeper's `is_keeper` to badge kept picks. See "There is no keeper
  league type" in `src/lib/utils/CLAUDE.md`.
- **Two rules the league decided here, in the constitution, that the draft board predates:**
  when two keepers owe the same round the *manager chooses* which one moves up; and draft
  picks trade **one for one**, so every team enters the draft with the same total number of
  picks, though rounds may still be lopsided.
- **The same-round collision rule diverges from the keeper draft board on purpose.** The
  constitution says the manager picks which keeper moves up; the draft board resolves it
  automatically by player rank (its `CLAUDE.md` calls that tie-break a tool-author guess).
  Garrett has accepted the divergence — the board is a planning aid, the constitution
  governs the actual draft — so **don't "fix" the board to match, and don't file it as a
  bug.** If the board's behaviour ever does change, this note and the board's own caveat
  both need updating.
- **Champions:** 2022 `paulslaats`, 2023 `kshoyer`, 2024 `BBrown16`, 2025 `malstol`.
- **Final standings are derived, not hand-kept** — `final_standings` in
  `static/data/league-history.json`, computed from the playoff brackets. Sleeper marks
  placement games with `p` (winners bracket p=1 is the title game, p=3 third place; the
  losers bracket repeats it for 5th–8th). The two teams in neither bracket finish 9th and
  10th, ordered by regular-season record then points for.
- **The hand-maintained 2025 list had 5th and 6th swapped.** It read `... kshoyer,
  mikestreinz, BBrown16, jonahcartwright ...`; the bracket says **BBrown16 5th,
  mikestreinz 6th** — BBrown16 won the consolation final over mikestreinz. The draft board
  still carries the swapped copy by hand in `~/Desktop/ff_keeper/src/ui/rosters.ts`; fix
  it there or, better,
  read `final_standings` instead of maintaining a second list.
- **2026 managers** — `managerID` values for `leagueInfo.js` are Sleeper `user_id`s, not
  roster IDs:
  | Roster | Handle | user_id | Team name |
  | --- | --- | --- | --- |
  | 1 | Gurret (Garrett — repo owner / commissioner contact) | `76909640692416512` | Slim Pickens 👱‍♀️💋🎀✨ |
  | 2 | TnT44 | `611697269254791168` | — |
  | 3 | mikestreinz | `605683461667229696` | Tupac on da bench |
  | 4 | tuckersdumbteam | `611664340277383168` | — |
  | 5 | paulslaats | `870570674836656128` | Street Clothes |
  | 6 | jonahcartwright | `612407006212468736` | StepBurrow I'm Stuck |
  | 7 | kshoyer | `611630747161358336` | — |
  | 8 | BBrown16 | `999190763323944960` | Straight Miss Pissles |
  | 9 | Kabroa | `611649934390870016` | #FREEJT |
  | 10 | malstol | `850475150817234944` | Ben's Beautiful Johnsons |

  Team names were re-checked against Sleeper on 2026-10-03. They are a snapshot: managers
  rename freely, and the site reads them live, so nothing in the repo needs changing when they
  do. kshoyer, tuckersdumbteam and TnT44 have none, so the site shows their handles.
  Roster IDs are listed for orientation only — **use `managerID`**. Roster IDs can shift
  between seasons, which is why the template deprecated the `roster` field.
- **One former manager.** `JJJet` (`860365948673204224`) is **Jordan Leonard**; he played
  2022 only, went 5-10, finished 9th, and was replaced by `BBrown16` in 2023. He IS in
  `managers`, last in the array, and `AllManagers` renders him in the **Moratorium** —
  a separate section it derives from Sleeper (no roster in the current season), not from
  any flag. He also appears in all-time records and the Rivalry dropdowns, which walk the
  full history regardless.
  `Football_Team` (`612343067143389184`) is **not** a former manager — the account is in
  the 2022 league's user list but never held a roster (`users_without_roster` in
  `static/data/league-history.json` confirms it, and its career record is 0-0). Don't add
  it to `managers`.

## The history dataset (`static/data/`)

`scripts/pull-league-history.py` pulls every season out of Sleeper into six JSON files —
1,233 transactions, weekly roster snapshots for every completed week (75 as of 2026 week 3),
player ownership timelines, and keeper chains. `derive-site-data` adds two more for the site.
See `static/data/README.md` for the shapes, and "The data pipeline" below for how they are
built. Nothing there is hand-edited.

`weeks.json` is the useful one for authoring: it snapshots every roster, starter and
per-player score for every week, so you can reconstruct the league at any point ("week 5 of
2024") rather than replaying transactions. The site never fetches it; `games.json` is its
browser-sized distillation.

Two facts the dataset settled, both of which contradicted earlier assumptions:

- **2022 has two drafts on the same league, and one isn't a 2022 draft.** The 14-round
  draft of 2022-09-04 (18 keepers) is the real season draft, flagged `primary`. The
  15-round one dated 2022-06-25 is the **previous season's draft, carried over from the
  league's earlier home on another platform** — Sleeper files it under 2022 because of the
  league it was attached to, and the date is the import, not the draft. It's the baseline
  2022's keeper costs price against. Merging the two silently corrupts every keeper cost.
  That draft is essentially all that survives of the pre-Sleeper season: no transactions,
  matchups or standings exist for it, so Sleeper history starts at 2022.
- **71 of 75 keepers match the constitution's cost rules exactly.** The four that don't:
  DeVonta Smith 2024 (tuckersdumbteam, R8 held instead of inflating to R7), De'Von Achane
  2024 (BBrown16, R13 rather than the expected R11), Amon-Ra St. Brown 2025 (mikestreinz,
  R4 — inflated despite a change of manager, which rule 4.3 says shouldn't happen), and
  Brian Thomas 2025 (jonahcartwright, R7 rather than R9). Probably commissioner
  adjustments; worth asking before treating them as precedent.

## The data pipeline

Three offline scripts, run in this order, each writing committed files:

```
python3 scripts/pull-league-history.py   # Sleeper -> league-history, weeks, transactions,
                                         #   ownership, keepers, players (static/data/)
npm run derive-site-data                 # -> games.json, season-notes.json (what pages fetch)
npm run derive-narratives                # -> narratives.json, docs/league-lore.md
```

The `mudd-data` skill runs all three in its refresh step, twice a week in season, so
`games.json` is at most a few days behind; pages built on it show a "through week N" stamp.
Standings' schedule luck instead builds the current season from live Sleeper matchups
(`liveSeasonGames`), so it can never lag the live table beside it.

- **The pull writes completed weeks only.** Sleeper serves every scheduled week of a season in
  progress — future weeks with every score `0.0`, and the current week partly scored, which
  passes any "was a point scored?" test. A current-season week counts only once the NFL week
  has moved past it (`completed_weeks()`), and the pull aborts rather than guess if
  `/state/nfl` comes back empty. That state is saved as `nfl_state` in
  `league-history.json`, so everything downstream is reproducible from the committed files.
- **The commissioner override is kept.** One game so far: 2024 week 8, tuckersdumbteam
  137.74 v BBrown16 122.54 (computed 150.34 to 148.74). The pull stores Sleeper's
  `custom_points` on the week snapshot, and every script scores games with
  `official_points()`: the override wins. That game's `max_pf` is null on both rows.
- **`STAT_CORRECTIONS`** in `derive-site-data.py` pins two small stat corrections made after
  settlement (2023 jonahcartwright v Gurret, 2024 Kabroa v tuckersdumbteam), so weekly sums
  match Sleeper's season records exactly.
- **`ELIGIBILITY`** in `derive-site-data.py` records the positions Sleeper actually allowed
  where `players.json` (today's position only) is wrong: Taysom Hill at TE/QB, Travis Hunter
  at WR in 2025. With it, the best legal lineup reproduces Sleeper's `potential_points` to the
  cent for all 50 manager-seasons; that is `max_pf` in `games.json`.
- **Self-checks fail the run before anything is written:** records and points against
  `league-history.json`, five games per regular-season week each seen from both sides, and
  `max_pf` against Sleeper to the cent.
- **One definition of everything.** `derive-narratives.py` imports `derive-site-data.py` as a
  module, and `scripts/week-facts.py` (the blog's fact block) imports `derive-narratives.py`,
  so all three share completed weeks, official scores, the optimal lineup,
  `STAT_CORRECTIONS` and `ELIGIBILITY`. Change those in `derive-site-data.py` only.

### End-of-season checklist

1. After the title game is final, re-run `python3 scripts/pull-league-history.py`, then
   `npm run derive-site-data`, then `npm run derive-narratives`. Every self-check must pass.
2. Commit the `static/data/` and `docs/league-lore.md` diffs together.
3. Check the new season's page at `/seasons/<year>` (final table, bracket, champion) and the
   Trophy Room.
4. Update the hand-written lines: Malcolm's bio in `leagueInfo.js` says "Reigning champion."
   (true only until the next title game), and each active bio's "Mudd League:" line is
   scoped to "2022 to 2025" and can be extended. Re-derive every figure; don't edit from
   memory. Also update `docs/mudd-voice.md`'s career figures and the Champions line in this
   file. The home page's champion panel updates itself.

### Preseason checklist

1. Swap the 4for4 FAAB guide in `src/lib/Resources/LeagueLinks.svelte`: its URL is the
   season's own article (`.../2026-...`), so it goes stale every year.
2. Check every external link still answers: `LeagueLinks.svelte`, the Keeper Draft Board in
   `tabs.js` and `homepageText`, and the FantasyPros and injury-report links.
3. Once the draft is done, re-run the pipeline so the new season's draft and keepers reach
   `league-history.json` and `keepers.json`.

## Commands

```
npm install          # node_modules is not checked in and not currently installed
npm run dev          # local dev server
npm run dev -- --host  # expose on the LAN to test on a phone
npm run build        # production build (Vercel adapter)
npm run preview
npm run lint         # BROKEN both halves, see below
npm run format       # prettier --write
npm run docker-run   # BROKEN, see below
```

Three gotchas, all verified locally and none caused by our config:

- **`npm run lint` is broken twice over.** The script is
  `prettier --check --plugin-search-dir=. . && eslint --ignore-path .gitignore .`
  Prettier exits 1 because 64 files (nearly all of them upstream's, including
  `CHANGELOG.md`) don't match its style, so `&&` means eslint never runs; and when it is
  run directly, ESLint 9 rejects `--ignore-path`, which flat config removed. Fixing this
  properly would mean reformatting 64 upstream files — exactly the whitespace-only diff
  the fork rules say not to create. Left alone deliberately. Use
  `npx prettier --check <specific file>` if you want to check something you wrote.
  We did add a `.prettierignore` so the ~880 KB of generated JSON in `static/data/`
  isn't linted; every `.md` in the repo is still flagged, which is pre-existing.

- **`npm run build` fails on Node > 22.** Compilation succeeds; the *Vercel adapter* then
  refuses the local Node version ("unsupported Node.js version: v25.9.0 ... use Node 18,
  20 or 22"). `engines` says only `>=v20.0.0`, which is why this is easy to trip over.
  Vercel's own builders are unaffected, so this blocks local verification, not deploys.
  To verify a build locally, run the node-adapter path directly:
  `DOCKER_BUILD=true npx vite build` — that completes cleanly.
- **`npm run build-docker` (and therefore `npm run docker-run`) is broken upstream.** The
  script is `vite build --verbose`, and this Vite version rejects `--verbose` as an
  unknown option before doing anything. Drop the flag if you need the container path.

Node **>= 20** (`engines`). `npm run prepare` compiles the Material theme into
`static/smui.css` / `static/smui-dark.css`; both are gitignored and regenerated on
install, so don't commit or hand-edit them.

Deployment is **Vercel** (`@sveltejs/adapter-vercel`, selected in `svelte.config.js`
unless `DOCKER_BUILD=true`). Push to `master` and Vercel builds it.

## Working in a fork (the constraint that shapes everything)

Upstream is actively maintained and this fork will want its fixes. Every edit should be
made so that `git merge upstream/master` stays boring:

- **Prefer configuration over code.** `src/lib/utils/leagueInfo.js`, the constitution
  page, and `static/managers/*` are the files upstream *expects* forks to change. Change
  those first, always, before touching a component.
- **Don't reformat, rename, or "tidy" upstream files.** A whitespace-only diff in a
  shared component is a merge conflict with no upside. The repo's existing style (4-space
  indent in `.svelte` files, mixed quoting) is upstream's; match the file you're in
  rather than the linter's opinion.
- **Keep league-specific additions in new files** where possible — a new component under
  `src/lib/`, a new route directory — rather than growing an upstream one.
- `src/lib/version.js` is marked **DO NOT EDIT** by upstream and is compared against
  `league-page.nmelhado.com` to surface an "update available" prompt. Leave it alone;
  it's the signal telling you when to pull upstream in.
- The `upstream` remote is configured (`https://github.com/nmelhado/league-page.git`).
  `git fetch upstream && git log --oneline HEAD..upstream/master` shows what's new. As of
  2026-10-03 (re-fetched) we are still level with it: our fork point `c25f29f` is upstream's tip.

### Inherited bugs fixed locally — keep these through a merge

Four upstream bugs are fixed in this fork. **Do not send them upstream: contributing back
was considered and declined.** They are documented because they explain why these files
diverge from `upstream/master`, and because a careless `git merge upstream/master` could
quietly reintroduce any of them — when resolving conflicts in these files, keep our side.

- **`goto()` throws on external URLs.** SvelteKit 2 refuses them
  (`@sveltejs/kit` 2.16.1, `client.js:1847`), so any tab pointing off-site dies. Upstream
  hit this and fixed *only the footer*, *only by label* — their newest commit is literally
  "Fix Go to Sleeper link in Footer.svelte (#364)", which special-cases
  `child.label == "Go to Sleeper"`. Both navs were left broken, and the label test breaks
  the moment a second external tab exists (ours: the Keeper Draft Board). We test the
  destination instead, in `NavLarge`, `NavSmall` and `Footer`.
- **`.manager:hover` never applied.** `ManagerRow.svelte` used `bar(--g999)` / `bar(--eee)`;
  `bar()` is not a CSS function, so both declarations were discarded. The tokens exist —
  it was only the function name.
- **`getTeamNameFromTeamManagers` was unguarded**, while its neighbour
  `getAvatarFromTeamManagers` guards the same lookup. Throws for a manager with no roster
  in the resolved season, which is exactly what a departed manager is.
- **`getLeagueTransactions` crashed on a failed Sleeper fetch.** `combThroughTransactions`'
  `.catch(console.error)` leaves its result undefined and the next line destructured it:
  "Cannot destructure 'transactionsData'", which took /manager down (and the nflState fetch
  beside it threw the same way on `season_type`). `leagueTransactions.js` now degrades to no
  transactions, uncached, so the page renders without them.

### Upstream files that now differ (the 2026-10 revamp)

Beyond the bugs above, the revamp edited many upstream files on purpose. Each was the smallest
edit that made the page readable on a phone, linked it to the rest of the site, or gave it a
real heading; nothing was reformatted. **Policy for the next `git merge upstream/master`: in
every file below, keep our side**, then re-apply any genuine upstream fix to it by hand. Run
`git diff upstream/master --stat` for the authoritative list; this is the map of why.

- **Shell and nav.** `Nav/index.svelte` (tab title through `pageTitle.js`, sticky phone bar),
  `NavLarge` and `NavSmall` (groups, a highlight that follows the page, the inert closed
  dropdown, a real hamburger button, 44px items), `Footer.svelte` (external links by
  destination, 44px links, every off-site link in a new tab), `tabs.js`, `app.html` (one light stylesheet), and
  `_smui-theme.scss` (its one `@use 'tokens';` line).
- **Matchups.** `Matchup.svelte`, `MatchupsAndBrackets`, `MatchupWeeks`, `Brackets`,
  `BracketsColumn`: no text shrunk below 12px, stacked scores on phones, a real
  regular/playoffs toggle, team names linking to manager pages, two columns above 1200px.
- **Records.** `RecordsAndRankings`, `Records/index`, `PerSeasonRecords`, `RecordTeam`,
  `BarChart.svelte`: the `:global` shrink rules deleted, `SegmentedControl` pickers instead of
  SMUI button groups, sortable ranking tables, each record's year linking to its season.
- **Standings.** `Standings/index` (division and tie columns dropped, Team column pinned on
  phones, side by side with schedule luck above 1200px) and `Standing.svelte` (the row's team
  is a real link).
- **Drafts.** `Drafts/index.svelte` was **rewritten** (about 60 lines): the completed draft
  leads in season, the projected board sits behind a `Disclosure`, and the carried-over 2021
  draft is labelled as such. `Draft.svelte` (no inner 70vh scroll on phones), `DraftRow.svelte`
  (the keeper badge), and `leagueDrafts.js` (`keeper` on each cell, and `draftID` for the
  2021 label).
- **Rivalry.** `Rivalry/index` ("Comparison", heading moved to the route) and
  `ManagerSelectors` (real names, unique ids, 44px selects, `Football_Team` filtered out).
- **Trades & Waivers.** `TransactionsPage`, `Transactions` (a real "view more" link),
  `TradeTransaction`, `WaiverTransaction`, `TransactionMove` (12px position labels),
  `Pagination.svelte` (44px arrows, scroll target below the sticky bar), and
  `leagueTransactions.js` (the crash guard above).
- **Blog.** `Posts`, `Post`, `FullPost`, `HomePost`, `AuthorAndDate` ("The Mudd Report",
  heading line-height, an 800px measure, comments gated on `enableComments`), and the three
  blog API routes (content type IDs from `contentfulTypes`).
- **Trophy Room.** `Awards.svelte` (one name, podium names below the avatars on phones,
  earlier seasons folded away, year headings linking to `/seasons/<year>`) and
  `leagueAwards.js`.
- **Managers.** `AllManagers` (the Moratorium), `Manager` (two columns above 1100px, career
  band, This week line, career-finish chips), `ManagerAwards`, `ManagerFantasyInfo` (Rival and
  Head-to-head links), `ManagerRow` (the `bar()` fix above, the card layout).
- **Rosters.** `Roster`, `RosterRow` (12px text, an anchor per team for the jump chips).
- **News and Resources.** `News/index`, `SingleNews` (44px links; links inside
  an article body open in a new tab), `Resources.svelte` (heading
  moved to the route), `news.js` (the dead Reddit feed degrades; see
  `src/lib/utils/CLAUDE.md`).
- **`Bar.svelte`** (the name is a real link) and **`universalFunctions.js`** (the guard above).
- **The data layer barrel.** `helper.js` re-exports `leagueGames.js` and `seasonNotes.js`.
- **Route files.** `+page.svelte` (the home page; see below), and the route files for awards,
  blog, blog/[slug], constitution, drafts, free-agents, manager, managers, records, resources,
  rivalry, rosters, standings and transactions. Most only mount `PageHeader`; `manager` and
  `blog/[slug]` also return a `title` from `load()`, and `standings` and `rivalry` load
  `games.json` for schedule luck and the head-to-head grid.

Ours outright, so they cannot conflict: `FreeAgents/`, `Design/`, `History/`, `Seasons/`,
`StatLab/`, `Home/`, `Resources/`, `Awards/HallOfFame.svelte`, `Standings/LastSeason.svelte`,
`Managers/ManagerThisWeek.svelte`, `Rosters/TeamChips.svelte`, the new helpers and utils, `src/theme/_site.scss`, and everything
under `src/routes/seasons` and `src/routes/stat-lab`.

## Architecture

SvelteKit 2 + Svelte 5 (running Svelte 5, but the components are written in **Svelte 4
idiom** — `export let`, `<slot />`, stores — with a few Svelte 5 event attributes mixed
in. Match the file you're editing; don't migrate components to runes wholesale).

```
src/
  routes/           # SvelteKit file-based routes; each page dir is +page.js + +page.svelte
    +page.svelte    #   the HOME PAGE (league text, power rankings, champ, transactions)
    +error.svelte   #   404 page; its tab title is "Not found" (pageTitle.js)
    seasons/        #   ours: /seasons index and /seasons/[year], 2021 (ESPN) to the current year
    stat-lab/       #   ours: /stat-lab, filter / sort / chart over games.json
    +layout.svelte  #   Nav + <slot/> + Footer, plus Vercel analytics
    api/            #   server endpoints (blog comments, players, news, version check)
    constitution/   #   hand-written league rules — pure content, edit freely
  lib/
    components.js   # barrel: every shared component is exported from here
    stores.js       # svelte writable stores used as the in-memory data cache
    utils/
      leagueInfo.js #   ** the config file — league ID, name, homepage text, managers **
      helper.js     #   barrel re-exporting everything from helperFunctions/ + leagueInfo
      helperFunctions/  # the Sleeper API data layer (see src/lib/utils/CLAUDE.md), plus our
                    #   static-data readers leagueHistory.js, leagueGames.js, seasonNotes.js
      tabs.js       #   nav structure, plus findTab / currentDest / tabAliases
      pageTitle.js  #   ours: the browser tab title (error page, load() title, nav label)
      managerLink.js #  ours: managerHref() -- a real /manager?manager=N href for a team
    Design/         # ours: primitives with their own barrel (see "The design system")
    History/        # ours: AllPlayTable, ScheduleLuck (Standings), HeadToHeadGrid (Rivalry)
    Seasons/        # ours: the Seasons archive -- SeasonPage, SeasonsIndex, seasonData.js, ...
    StatLab/        # ours: Stat Lab -- Lab, statLab.js, hand-written SVG charts, DataTable
    Home/           # ours: SeasonMilestone (trade deadline, then playoffs, on the home rail)
    Resources/      # ours: LeagueLinks, mounted above upstream's Resources.svelte
    <Feature>/      # one directory per feature (Standings, Records, Matchups, …)
  theme/            # SMUI (Material) SCSS theme
    _tokens.scss    #   OUR design tokens, @use'd by _smui-theme.scss in one line
    _site.scss      #   OUR global rules, @use'd by _tokens.scss
    dark/           #   still compiled by `npm run prepare`, no longer served
static/             # images, PWA manifest, favicons, static/managers/ for bios
```

Data flow: a route's `+page.js` `load()` calls helper functions, which fetch Sleeper and
memoize into `src/lib/stores.js`, and returns **unawaited promises**; the `.svelte` file
resolves them with `{#await}` blocks so the shell renders immediately. Keep that shape —
`await`ing in `load()` blocks the whole page on the slowest call.

## The home page specifically

`src/routes/+page.svelte` is a two-column layout above 950px: league name + `homepageText` +
the featured blog post + `<PowerRankings />` on the left, and a right rail with the NFL-state
banner (a link to /matchups), the draft countdown or, once the draft is done,
`SeasonMilestone` ("Trade deadline · N weeks away", then the playoffs), the reigning champion
(from `getAwards()`, one `<a class="champLink">`), and recent `<Transactions />`.

**On phones it is one column in reading order, not two stacked boxes.** Every block is a flex
item of `#home`, and CSS `order` interleaves the columns: intro, week banner, milestone, power
rankings, champion, blog post, transactions. That brought power rankings from y≈1810 to ≈930
at 375px. A new home block needs an `order` too, or it falls to the end on phones.
`SeasonMilestone` has no ticking clock on purpose: Sleeper closes trades when week 12's last
game ends and publishes no time for it.

The template's intent is that you customize it **through `homepageText`** (an HTML string
in `leagueInfo.js`, injected with `{@html}`) rather than by rewriting the component. Do
that first. Only restructure `+page.svelte` when the content genuinely doesn't fit the
two-column shape — and see "Working in a fork" before you do.

Because `homepageText` is `{@html}`-injected, it is raw HTML: it can carry links (e.g. to
the keeper draft board) and markup, and it must be hand-written trusted content. Never
wire user input into it. Svelte's scoper never sees `{@html}` content, so its classes
(`homeLede`, `homeLinks`, `homeRules`) are styled from `src/theme/_site.scss`. There is no
hand-written champion paragraph any more; don't add one back, the right rail already says it.

## The design system

Added in the redesign; everything below is ours, not upstream's.

- **One light theme, no toggle.** `src/app.html` loads a single unconditional `/smui.css`.
  The `media="(prefers-color-scheme: light)"` attribute must stay OFF that link — with it, a
  dark-OS visitor gets no MDC CSS at all, and that is invisible when developing on a light
  machine. `src/theme/dark/` is still compiled by `npm run prepare` and simply never served;
  deleting it would conflict on every future upstream merge.
- **Tokens live in `src/theme/_tokens.scss`**, pulled in by one `@use 'tokens';` line so
  upstream's `_smui-theme.scss` stays mergeable. Radius scale, `--shadowCard`, a navy ramp and
  a gold accent. **`--navy400` (`#0082c3`) fails AA at 3.54:1** — large text, borders and icons
  only; use `--accentInk` (`#005a94`, 6.10:1) for anything smaller. Gold is a fill, never ink.
  **`npm run dev` does not recompile Sass** — run `npm run smui-theme-light` after every edit
  or nothing changes.
- **Type**: Oswald for headings, MDC buttons and nav tabs, via the
  `--mdc-typography-*-font-family` hooks — no component edits needed, since the compiled sheet
  emits those hooks on the bare `h1`–`h6` selectors. Never set the base
  `--mdc-typography-font-family` or `subtitle1`; they reach body text, list items and inputs.
  Data-table cells use Roboto's tabular figures; real Roboto Mono is reserved for `StatTile`,
  because its wider glyphs overflow the hardcoded name-cell widths in Roster and Records.
- **Brand art lives in `static/brand/`** — the seal (full and small), wordmark, laurel and the
  Trophy Room ribbon, all hand-authored SVG, documented in `static/brand/README.md`. Three traps
  live there: an SVG loaded through `<img src>` gets **no page CSS and no webfonts**, so colours
  are literal hex kept in step with the tokens by hand and any text pins its width with
  `textLength`; `banner.svg` deliberately carries **no text** because the heading is real markup
  in `Awards.svelte`; and an XML comment containing two consecutive hyphens is a parse error that
  blanks the whole file.
- **The raster icons are generated, not drawn.** `node scripts/render-icons.js` renders every
  favicon, the PWA icons and a hand-assembled `favicon.ico` from `seal-simple.svg`; its output is
  committed and it is deliberately **not** part of `npm run build`. Re-run it after changing the
  mark. It insets the two android-chrome icons to 72% because `manifest.json` declares them
  `maskable`, and Android crops those to a circle keeping only the central 80% — full-bleed would
  shave the gold ring off. `sharp` is a devDependency and Vercel never runs it.
- **The 12px / 44px floor is a standing rule.** Nothing renders below 12px, table data at
  least 14px, and every interactive target is at least 44px tall on phones and touch screens
  (inline links in prose and third-party news content excepted). When something doesn't fit,
  change the layout (stack it, or scroll it inside its own container with a sticky first
  column), never the type size. Every page met it at 375px after the 2026-10 revamp; check new
  work with the snippet at the end of `docs/plan-site-todo.md`.
- **League-owned global rules live in `src/theme/_site.scss`**: layout fixes and overrides of
  upstream `:global(...)` rules, so the upstream component can stay as it is. `_tokens.scss`
  `@use`s it at the top (Sass requires `@use` before any rule), so it reaches the build with no
  line added to an upstream file; like the tokens it reaches the light build only. It **cannot**
  override a scoped rule (the hash class wins), so for those edit the component and keep the
  diff small. It also holds the footer fix that stopped pages jumping as they load (`<main>` is
  a screen tall and the footer hangs below it), the 44px `.mdc-button` rule for touch, and the
  `homepageText` styles. **`--stickyBar`** (61px below 951px, 0 above) is the height of the
  sticky phone nav: anything that scrolls to an in-page target uses
  `scroll-margin-top: var(--stickyBar)` or reads it for `window.scrollTo`, or lands under the bar.
- **Primitives in `src/lib/Design/`** (`Card`, `StatTile`, `SectionHeading`,
  `SegmentedControl`, `Countdown`, `PageHeader`, `Disclosure`) with **their own barrel** —
  deliberately not `$lib/components`, which is byte-identical to upstream and gains entries
  most releases. `SectionHeading` styles a *class*, never a tag selector: it renders through
  `<svelte:element>`, where Svelte's scoper silently strips tag rules it cannot see.
  - **`PageHeader`** is the title block on every page (eyebrow, title, one-line intro). Mount it
    in the **route file**, so it paints before the data and upstream components only ever lose
    their old heading.
  - **`Disclosure`** is a real `<button aria-expanded>` that mounts its content only when
    opened (the projected draft board, the Trophy Room's earlier seasons). Not `<details>`,
    because hidden-but-mounted heavy components still cost layout and images.
  - **`SegmentedControl`** now takes 2–7 options and **wraps** instead of overflowing (seven
    labels don't fit a 375px row, and a sideways-scrolling group hides its own options), with a
    fixed 28px radius so a two-row group doesn't grow half-circle ends. Segments are 44px tall
    on phones and touch screens and keep the compact size for a mouse. Its API is unchanged.

## The nav

`src/lib/utils/tabs.js` is the whole structure; read its header comment before editing.

- **Top bar:** Managers, Matchups, Standings, Free Agents, Trades & Waivers, Blog, League ▾.
  There is **no Home tab** (the seal links home; dropping it is what let Free Agents be
  promoted and all seven fit above 950px, with 12px tab padding up to 1100px).
- **League ▾** holds three groups, written as `{ group: 'History' }` entries: **This Season**
  (Rosters), **History** (Seasons, Trophy Room, Records, Rivalry, Drafts, Stat Lab) and
  **Rules & Tools** (Constitution, Keeper Draft Board, Resources, Go to Sleeper). NavLarge shows
  a group as a caption, NavSmall as a Subheader, the footer drops it. Off-site entries are
  detected by URL, open in a new tab and carry an ↗ icon.
- **The desktop dropdown** is measured on every open, capped to the room below the tab (it
  scrolls inside itself on a 1024×768 screen), and `inert` and `visibility: hidden` while
  closed, because closing only squashes it to `max-height: 0`.
- **The highlight follows the page**, via `findTab` / `currentDest`: a path matches a tab or
  one of its children, `tabAliases` maps `/manager` to Managers, and a nested path with no tab
  of its own falls back to its first segment (`/seasons/2024` lights Seasons,
  `/blog/<slug>` lights Blog). The same lookup gives the tab title (`pageTitle.js`), so a
  label is also a page title.
- **Phones:** a sticky 61px bar (seal plus a real 44px menu button); the menu's items are 44px
  and pass contrast.
- **Label constraints still apply:** exactly one `nest: true` tab; the Blog tab must stay
  top-level and keep the label `Blog` (it is hidden by that label while `enableBlog` is false);
  Managers is hidden by its label when `managers` is empty.

## Conventions

- Import shared things from the barrels — `$lib/components` and `$lib/utils/helper` —
  not by deep path. That's how the whole codebase does it.
- New shared components: add the file under `src/lib/<Feature>/`, then export it from
  `src/lib/components.js`.
- Manager photos go in `static/managers/` and are referenced from `leagueInfo.js` as
  `/managers/<handle>.<ext>`. Square, no larger than 500x500. They are named after the
  **Sleeper handle**, not the display name, so renaming a manager can't orphan their photo.
  All ten are served locally on purpose — they began as Sleeper avatars, but a
  `sleepercdn.com/avatars/<hash>` URL breaks the moment a manager changes their avatar.
  Most are `.webp`; `gurret` is `.jpg`. Sleeper's `Content-Type` is unreliable (it returned
  `image/png` for JPEG bytes), so sniff magic bytes rather than trusting the header.
- Secrets (`VITE_CONTENTFUL_*`) live in a gitignored `.env` locally and in Vercel's
  environment variables in production. The blog is **on** (`enableBlog = true`), reading
  Contentful with the read-only delivery token; comments are off (see the status list).
  `CONTENTFUL_MANAGEMENT_TOKEN`, used only by `scripts/publish-article.mjs`, is deliberately
  not `VITE_`-prefixed and lives only in the local `.env`, never in Vercel.
- Sleeper's API is public, read-only, and unauthenticated. There is no write path to
  Sleeper from this site, and there shouldn't be one.
