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

**Status: live at [mudd-league.vercel.app](https://mudd-league.vercel.app).** Every push to
`master` deploys. `leagueInfo.js` is fully configured; all eleven managers (ten active plus
Jordan Leonard in the Moratorium) have real names, hometowns, locally-served photos and
bios; the constitution is this league's rules; the shell is rebranded.

Still outstanding, in rough priority order:

- **The blog is off.** `enableBlog = false` and it needs a Contentful space that doesn't
  exist yet — see `docs/blog.md`. The three weekly posts and the skill to draft them are
  planned (`docs/post-generator-skill.md`), not built.
- **`static/data/` is read in exactly one place.** `helperFunctions/leagueHistory.js` fetches
  `league-history.json` (memoized, SSR-safe) for the manager career band and the Hall of Fame.
  It is the only source for a full 1–10 finish — Sleeper exposes podium and toilet bowl only —
  and it keys on `user_id`, which sidesteps roster IDs moving between seasons. The other five
  files, `weeks.json` above all, are still unread; that one holds per-player weekly scores for
  every week of 2022–25 and is the only way to get a season MVP or a championship final score.
- **Sortable record tables were considered and rejected for the six *record* tables.** Each is
  a top-N list defined by its own metric, and the rank column is positional (`{ix + 1}`), so
  re-sorting renumbers rank into nonsense. The four *ranking* tables (Win %, Points, Lineup IQ,
  Transactions) would genuinely benefit and remain unbuilt.
- **Optional manager fields are unset** — `favoriteTeam`, `preferredContact`,
  `fantasyStart`, `philosophy`, `tradingScale`. Each renders as a muted "?" placeholder.
  `rival` is "The Field" for everyone; real rivalries need `rival.link` set to another
  manager's *index* in the array.

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
try to unify them. This site links to the board from `tabs.js`, under League Info.

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
  6 bench, 2 IR. Playoffs: 4 teams, starting week 16. Waivers: FAAB, $100 budget.
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
  | 1 | Gurret (Garrett — repo owner / commissioner contact) | `76909640692416512` | Slim Pickens |
  | 2 | TnT44 | `611697269254791168` | — |
  | 3 | mikestreinz | `605683461667229696` | Tupac on da bench |
  | 4 | tuckersdumbteam | `611664340277383168` | — |
  | 5 | paulslaats | `870570674836656128` | Street Clothes |
  | 6 | jonahcartwright | `612407006212468736` | StepBurrow I'm Stuck |
  | 7 | kshoyer | `611630747161358336` | — |
  | 8 | BBrown16 | `999190763323944960` | JustHereSoIWon'tGetFined |
  | 9 | Kabroa | `611649934390870016` | #FREEJT |
  | 10 | malstol | `850475150817234944` | Ben's Beautiful Johnsons |

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
1,155 transactions, weekly roster snapshots for all 72 played weeks, player ownership
timelines, and keeper chains. See `static/data/README.md` for the shapes. Re-run it after a
season and commit the diff. Nothing there is hand-edited.

`weeks.json` is the useful one: it snapshots every roster, starter and per-player score for
every week, so you can reconstruct the league at any point ("week 5 of 2024") rather than
replaying transactions. Nothing in the site reads these files yet.

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
  2026-08-10 we are level with it: our fork point `c25f29f` is upstream's tip.

### Inherited bugs fixed locally — keep these through a merge

Three upstream bugs are fixed in this fork. **Do not send them upstream: contributing back
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

## Architecture

SvelteKit 2 + Svelte 5 (running Svelte 5, but the components are written in **Svelte 4
idiom** — `export let`, `<slot />`, stores — with a few Svelte 5 event attributes mixed
in. Match the file you're editing; don't migrate components to runes wholesale).

```
src/
  routes/           # SvelteKit file-based routes; each page dir is +page.js + +page.svelte
    +page.svelte    #   the HOME PAGE (league text, power rankings, champ, transactions)
    +layout.svelte  #   Nav + <slot/> + Footer, plus Vercel analytics
    api/            #   server endpoints (blog comments, players, news, version check)
    constitution/   #   hand-written league rules — pure content, edit freely
  lib/
    components.js   # barrel: every shared component is exported from here
    stores.js       # svelte writable stores used as the in-memory data cache
    utils/
      leagueInfo.js #   ** the config file — league ID, name, homepage text, managers **
      helper.js     #   barrel re-exporting everything from helperFunctions/ + leagueInfo
      helperFunctions/  # the Sleeper API data layer (see src/lib/utils/CLAUDE.md)
      tabs.js       #   nav structure
    <Feature>/      # one directory per feature (Standings, Records, Matchups, …)
  theme/            # SMUI (Material) SCSS theme
    _tokens.scss    #   OUR design tokens, @use'd by _smui-theme.scss in one line
    dark/           #   still compiled by `npm run prepare`, no longer served
static/             # images, PWA manifest, favicons, static/managers/ for bios
```

Data flow: a route's `+page.js` `load()` calls helper functions, which fetch Sleeper and
memoize into `src/lib/stores.js`, and returns **unawaited promises**; the `.svelte` file
resolves them with `{#await}` blocks so the shell renders immediately. Keep that shape —
`await`ing in `load()` blocks the whole page on the slowest call.

## The home page specifically

`src/routes/+page.svelte` is a two-column layout: league name + `homepageText` +
`<PowerRankings />` on the left, and a right rail with the NFL-state banner, the reigning
champion (from `getAwards()`), and recent `<Transactions />`.

The template's intent is that you customize it **through `homepageText`** (an HTML string
in `leagueInfo.js`, injected with `{@html}`) rather than by rewriting the component. Do
that first. Only restructure `+page.svelte` when the content genuinely doesn't fit the
two-column shape — and see "Working in a fork" before you do.

Because `homepageText` is `{@html}`-injected, it is raw HTML: it can carry links (e.g. to
the keeper draft board) and markup, and it must be hand-written trusted content. Never
wire user input into it.

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
- **Primitives in `src/lib/Design/`** (`Card`, `StatTile`, `SectionHeading`,
  `SegmentedControl`, `Countdown`) with **their own barrel** — deliberately not
  `$lib/components`, which is byte-identical to upstream and gains entries most releases.
  `SectionHeading` styles a *class*, never a tag selector: it renders through
  `<svelte:element>`, where Svelte's scoper silently strips tag rules it cannot see.

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
  environment variables in production. The blog is **off** (`enableBlog = false`) and
  needs Contentful before it can be turned on.
- Sleeper's API is public, read-only, and unauthenticated. There is no write path to
  Sleeper from this site, and there shouldn't be one.
