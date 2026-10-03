# Site revamp: order and log

Started 2026-10-02 on the local branch `site-revamp`. Nothing gets pushed until Garrett has
reviewed it; every push to `master` deploys.

The plans being carried out:
- [`plan-site-todo.md`](plan-site-todo.md): workstreams A–F
- [`plan-history-pages.md`](plan-history-pages.md): History steps 0–4
- [`site-todo.md`](site-todo.md): the list both plans come from

## Order

| Step | Work | Why here | Status |
| --- | --- | --- | --- |
| 1 | **A. The nav**, plus the voted 2026 roster-change text (F) | Every page benefits; the new pages need its groups; the roster text is wrong on the live site today | done |
| 2 | **C1–C3.** Records, Matchups, Standings readable on phones; creates `src/theme/_site.scss` | The worst phone problems, on the most-used pages | done |
| 3 | **History step 0 + 1.** The game table, then schedule luck on Standings | Foundation for four pages; most useful mid-season | step 0 done (merged); step 1 merged into step 4 |
| 4 | **B1–B3 + schedule luck.** `PageHeader` on every page, text fixes, the page jumping as it loads, then the all-play table on Standings | Both edit the Standings route; History pages reuse `PageHeader` | done |
| 5 | **D.** Links between pages, plus **History step 2**, the head-to-head grid | Both work on Rivalry and manager links | done; lore-script fix done (merged) |
| 6 | **C4–C5 + B4–B5.** Drafts, remaining small text and tap targets, blog typography, desktop layouts | Polish on less-used pages | done |
| 7 | **E. Content:** bio typos and league lines (7a, running in parallel in a worktree, Opus); home page copy, Resources, countdown (7b) | Writing, once the page frames are settled | done (home copy approved 2026-10-03) |
| 8 | **History step 3.** Seasons archive | Biggest new page | done (merged) |
| 9 | **History step 4.** Stat Lab, first release | Built on everything above | done |
| 10 | **F wrap-up.** `CLAUDE.md` corrections, end-of-season checklist, `mudd-preview` post type, full-site audit | Docs describe the finished state | done |

## Decisions already made (2026-10-02)

- The 2026 roster change was **voted 7–3**: five bench spots, thirteen roster spots, a
  thirteen-round draft.
- Drop the Home tab. Follow the plan's other nav recommendations.
- The constitution's missing rules are dropped; don't invent rules.
- Move the news feed to the bottom of Resources.
- Leave "Marvey Mudd" (Malcolm's bio) and the Tucker and Kevin bio questions alone.
- The home page copy is written by the step-7 agent and reviewed by Garrett before any push.

## Log

_Each step adds what was done, what was found, and any changes to the remaining plan._

### Step 1: nav and roster text (done, Opus, about 21 minutes)

Commits `3e70099`..`0674023`, 13 files. The node-adapter build passes.

- **Top bar:** Managers, Matchups, Standings, Free Agents, Trades & Waivers, Blog, League ▾.
  - Home is dropped.
  - Tab padding is 12px between 951px and 1100px so all seven tabs fit (885px).
- **League menu:** grouped into This Season, History and Rules & Tools. Off-site links show ↗.
- **Highlight** follows client-side navigation. /manager lights Managers. Each dropdown item is
  marked when it's the current page.
- **Tab titles** match the nav labels. Manager pages show the manager's name; blog posts show
  the post title.
- **Phone menu:**
  - a real 44px button;
  - items at 7.46:1 contrast and 44px tall;
  - a sticky 61px bar on phones only.
- **Roster change:** five bench spots and thirteen rounds, with an amendment note in the
  constitution.

**Changes to the remaining plan:**
- **Sticky bar offset.** Anything that sticks or jumps to an in-page anchor on phones must
  allow for the 61px bar. Steps 2, 4 and 6 carry this.
- **Footer links** are 37px tall: added to C5 (step 6).
- **Layout shift** measured 0.72 on /standings at 375px: B3 (step 4) owns it.
- **The blog can't be checked locally:** there's no Contentful token in `.env`. Check B4's
  blog typography by reading the code, or against the live site.
- **New pages in the nav:** Seasons and Stat Lab go under `{ group: 'History' }`. Titles and
  highlighting then work automatically, through a first-segment fallback.
- **Dropdown accessibility.** The desktop dropdown's items stay in the DOM while hidden, which
  predates this work. Possibly reachable by screen readers. Added to step 10's audit.

### Step 2: Records, Matchups, Standings on phones (done, Sonnet, about 18 minutes)

Commits `901adce`..`f587e7e`.

- **At 375px:** nothing under 12px, table data at least 14px, no sideways scrolling, 44px
  segment buttons.
  - /records: 6.3px → 12px.
  - /matchups: 5.6px → 12px.
  - /standings: fits without scrolling.
- **New global stylesheet** `src/theme/_site.scss`, loaded from `_tokens.scss`.
- **`SegmentedControl`** wraps instead of overflowing, and is 44px on phones. Its API is
  unchanged.
- **Standings** drops its division and tie columns, and the Team column stays in view.
- **Six previously untouched upstream files** gained edits: `Matchup.svelte`, `Brackets`,
  `BracketsColumn`, `PerSeasonRecords`, `RecordTeam` and `BarChart`. Step 10 lists them in
  `CLAUDE.md`.

**Changes to the remaining plan:**
- **No `git stash` in this repo.** It emptied the index twice, in steps 1 and 2. Every prompt
  now forbids it.
- **`Manager.svelte`** still has its shrink rules and SMUI button groups: step 6.
- **Nav dropdown group captions** are 11.52px: step 6.
- **Standings on desktop** is now a small centred table: step 6's desktop layout pass.

### Step 0 (History): the game table (done, Opus, in parallel, about 19 minutes; merged as `88c1e89`)

- **Pull script:** now writes completed weeks only, and records `nfl_state`.
  - 2026 is weeks 1–3; week 4 is partial and left out.
  - Ownership spans and the narratives no longer include unplayed weeks. They had invented six
    0.0–0.0 "luckiest wins".
- **`games.json`:** 694 rows, 4.3 KB gzipped.
- **`season-notes.json`:** 4.0 KB gzipped.
- **Self-checks** pass for all 50 manager-seasons. The data is deterministic: re-running leaves
  no diff.
- **`max_pf` is left out.** Two seasons miss Sleeper's figure by more than 1%: Taysom Hill's and
  Travis Hunter's eligible positions changed. So Stat Lab has no max-points or bench measure.
- **`leagueGames.js`:** `getLeagueGames`, `filterGames`, `allPlay`, `headToHead`,
  `standingsFrom` and `liveSeasonGames`, exported from `helper.js`.

**Found in the data:**
- **A commissioner score override,** 2024 week 8, tuckersdumbteam v BBrown16 (`custom_points`).
  The pull keeps it now, but `derive-narratives.py` and `week-facts.py` still read `points`:
  added to step 10.
- **Four small stat corrections after settlement** are pinned in `STAT_CORRECTIONS`.

**Changes to the remaining plan:**
- **Step 3 is folded into step 4.** Both edit the Standings route, and the API is ready.
- **Bio work moved forward.** Step 7a (bio typos and league lines) runs in parallel now,
  because it needs no browser.

### Step 4: page headers, text fixes, layout shift, schedule luck (done, Sonnet, about 20 minutes)

Commits `78437cd`..`48e85ee`.

- **`PageHeader`** (`$lib/Design`) is on every page, with one-line intros in the league's
  voice. The full list of intros is in the agent's report.
- **Layout shift** is fixed with CSS only, in `_site.scss`:
  - /standings: 0.78 → 0.02 at 375px, 0.29 → 0.03 at 1024px.
  - /manager: 0.66 → 0 at 375px, 0.41 → 0 at 1024px.
- **Schedule luck** on Standings, using `AllPlayTable` (display only) and `ScheduleLuck` (live
  vs. preseason data).
  - Checked: every team's all-play is 27 games (9 × 3).
  - Luck sums to about 0.
  - tuckersdumbteam is 27-0; mikestreinz has the top luck at +1.56.
- **Small text fixes:**
  - Rivalry dropdowns show real names, and the duplicate ids are fixed.
  - The Mudd Report naming, "Comparison", "Upcoming", "All".

### Step 7a: bios (done, Opus, in parallel; merged as `95021d8`)

- **Typos fixed,** including 32/59 = 54.2%. The coordinator added a comma to the
  Northwestern line.
- **A Mudd League line for each of the 10 active managers.** Every figure was recomputed from
  the data, and none can go stale mid-season.

**Found:** the lore file and the voice doc carry wrong figures.
- Kabroa's "72.1 points left on the bench" (2025 week 15) was really 54.00. The real record
  is Kabroa's 69.78, in a 2022 week 17 consolation game.
- MVP and keeper "returned" figures count points scored on the bench.

A lore-script fix now runs in parallel with step 5.

**Changes to the remaining plan:**
- **Step 5:** filter `Football_Team` (never held a roster) out of the Rivalry dropdown and the
  grid, and turn the Standing rows' clickable div into a link.
- **Step 6:**
  - check the blog's pagination scroll target, now an empty div, by reading the code;
  - the Drafts h6 and the Awards division captions;
  - the Drafts h4s were kept, because step 6 reorders that page.
- **Step 8:** reuse `AllPlayTable` (not `ScheduleLuck`) on the Seasons pages.
- **Step 10:** list the newly diverged upstream files in `CLAUDE.md`: `News/index`,
  `Rivalry/ManagerSelectors`, `Drafts/Draft`, and the route files for rosters, rivalry, drafts,
  transactions, resources and records.

### Step 5: head-to-head grid and links between pages (done, Sonnet; interrupted by the usage limit and resumed)

Commits `8b2e678`..`0c6b971`.

- **Head-to-head grid** on Rivalry: a full grid above 960px, a picker and opponent list below.
  - Regular-season totals equal every manager's career W-L.
  - Four pairings match the Rivalry page.
  - Worst cell contrast is 7.5:1.
- **Manager pages:** the Rival tile links to the rival, with a separate Head-to-head link under
  it, and a "This week: vs …" line.
- **Matchup cards and brackets:** team names link to manager pages.
- **Real links** for the home NFL banner, the champion panel, Standings team names, Bar names
  and "view more".
- **New helper:** `$lib/utils/managerLink` (`managerHref`).

**Changes to the remaining plan:**
- **Step 6's small-text list grows:**
  - roster chips at 8.64px on /manager;
  - the "th" ordinal suffixes at 7.68px on /;
  - the nav group captions at 11.52px;
  - the Rivalry dropdowns at 30px tall;
  - footer links at 37px;
  - the #FREEJT row at 43px.
- **Step 6's two-column manager page:** keep `ManagerThisWeek` in the left column.
- **Step 7b:** the champion block is now one `<a class="champLink">`; keep that if the home
  layout changes.
- **Step 10:** add `Standing.svelte`, `Bar.svelte` and `Transactions.svelte` to the
  diverged-files list.

### Lore pipeline fix (done, Opus, in parallel; interrupted and resumed; merged)

- **`derive-narratives.py`** now imports `derive-site-data.py`, so both share completed weeks,
  official scores, the optimal lineup and `STAT_CORRECTIONS`.
- **Player value counts starter points only.** That changes:
  - TnT44's career MVP: Josh Jacobs 476.5, not Purdy 493.3;
  - Daniels: 325.9, not 396.6;
  - Purdy's 2023 keeper season: 190.66, not 353.6.
- **Bench maths:** a table of the positions Sleeper allowed (Taysom Hill, Travis Hunter) makes
  all 50 manager-seasons match Sleeper's `potential_points` to the cent.
- **The commissioner override** is applied everywhere.
- **Self-checks** exit before writing anything if a check fails.
- **294 facts**, down from 301; the 2026 comparisons are gone.
- **Voice doc:** the bench record line is fixed. kshoyer "shares" the best career record with
  Tucker (both 40-23 in the regular season).
- **Re-running the scripts after the merge** changes only timestamps.

**Changes to the remaining plan:**
- **Step 10:** `CLAUDE.md` says "278 facts"; it should be 294.
- **Optional:** adding the same eligibility table to `derive-site-data.py` would let
  `games.json` include `max_pf`. That unlocks max-points and bench measures in Stat Lab. Hand it
  to step 9 as optional.
- **For blog writers:** bench facts can't tell IR players apart, so check before mocking
  anyone.

### Step 6: Drafts, small text, blog, desktop layouts (done, Sonnet, about 30 minutes)

Commits `d9becd2`..`f0cb4f3`.

- **All 15 pages at 375px:** smallest font at least 12px, no sideways scrolling, interactive
  targets at least 44px. The one exception is the Free Agents checkbox; its label is 44px.
- **Drafts:** the completed draft leads, and the projected order sits behind a new
  `Disclosure` primitive.
- **Manager page:** two columns above 1100px.
- **Matchups:** two columns above 1200px.
- **Standings:** the table and schedule luck sit side by side above 1200px.
- **Rosters:** team jump chips.
- **Trophy Room:** earlier seasons are folded away (6,688px → 3,160px).
- **Blog typography,** checked against a temporary mock.
- **New `--stickyBar` token** (61px below 951px) for scroll targets.

### max_pf (done, Sonnet, in parallel; merged)

- **`games.json`** gains `max_pf`, the true best legal lineup. The script reproduces Sleeper's
  `potential_points` **to the cent for all 50 manager-seasons**, a check that now fails the
  script on any miss.
- **The override game** has null `max_pf` on both rows.
- **New `leagueGames.js` helpers:** `benchPoints`, `lineupEfficiency`, `lineupTotals`.
- **The eligibility table** now lives in `derive-site-data.py`, and `derive-narratives.py` uses
  it from there.

**Changes to the remaining plan:**
- **Stat Lab** gets max points, bench points and lineup efficiency (decision 3 is settled: the
  check holds).
- **Step 8** also relabels the carried-over 2021 draft on /drafts, which today shows as a
  second "2022 Draft".
- **Step 10:** `Drafts/index` was rewritten (about 60 lines), and many more upstream files now
  differ. See step 6's file list.

### Step 7b: home page, Resources, season milestone (done, Opus)

Commits `3270061`..`442c350`.

- **Home page:**
  - shorter `homepageText` with a "Find your way" row;
  - the rules are now one line linking to the constitution (every removed rule was confirmed
    to be in the constitution);
  - the hard-coded champion paragraph is gone;
  - phones get a new order: intro, week banner, milestone, power rankings, champion, blog,
    transactions;
  - at 375px, power rankings moved from y≈1810 to 929, and the champion from 2461 to 1492.
- **Resources:**
  - a new `LeagueLinks` component goes first;
  - a "Useful elsewhere" group: FantasyPros half-PPR weekly and rest-of-season rankings, the
    NFL injury report, and 4for4's 2026 waiver/FAAB guide. All return 200.
- **Season milestone:** no ticking countdown. Sleeper closes trades when week 12's last game
  ends, with no published time (Sleeper help article cited in a comment). So it shows a plain
  line: "Trade deadline · N weeks away", then "Playoffs · N weeks away".

**Changes to the remaining plan:**
- **Step 10:**
  - the 4for4 guide URL is for 2026; add swapping it to the preseason checklist;
  - `src/routes/CLAUDE.md`'s description of the home page is wrong on phones now;
  - list `src/lib/Home/` and `src/lib/Resources/`.
- **Optional for the Seasons pages:** the removed 2025 title write-up exists nowhere else now.

### Step 8: Seasons archive (done, Opus, in a worktree; merged as `734645d`)

- **Pages:** `/seasons` and `/seasons/[year]`, for 2021 (ESPN, carried-over draft only) through
  2026 (in progress).
- **Each year has:** final table, all-play, bracket, rank-by-week chart, draft rounds 1–3,
  keepers, trades and extremes.
- **Links in:** Trophy Room year headings, and career-finish chips on manager pages.
- **/drafts:** the 2021 draft is now labelled correctly.
- **Checks:**
  - all champions and finishes match;
  - all 32 bracket games match `games.json`;
  - 2022 shows 18 keepers;
  - all-play totals are 135 per team;
  - unknown years return a real 404.
- **Not done:** Records entries linking to their season.

### Step 9: Stat Lab (done, Opus, in parallel with step 8)

Commits `f93e917`..`3b83a00`.

- **Datasets:** Games, Seasons, Careers.
- **Measures:** 13, including max points, bench points and lineup efficiency.
- **Charts:** bar, line, scatter, with a sortable table under each.
- **Shareable views:** the whole state lives in the address; Back undoes presets and narrowing.
- **Six presets.** No new dependencies.
- **Checks:**
  - 2025 W-L matches all ten records;
  - the biggest week is mikestreinz's 193.04 (2023 week 5);
  - luck matches Standings.
- **Bench-total differences** against Sleeper in 6 of 50 seasons are all explained: the override
  game's null rows, the true best lineup beating Sleeper's own method for TnT44 (2023 and 2024),
  and the pinned stat corrections.
- **A second release could add:** a matchups dataset and grid, a distribution chart, a
  minimum-games control, and keyboard focus for line and scatter points.

### Step 10: docs, loose ends, full-site audit (done, Opus; interrupted by the usage limit and resumed)

Commits `47b8c47`..`9d46ad2`.

- **Docs:** all three `CLAUDE.md` files describe the finished site, including a list of the
  upstream files that now differ (keep our side on the next merge) and end-of-season and
  preseason checklists. `site-todo.md` is ticked off.
- **`mudd-preview`** publishes as type Preview.
- **Loose ends fixed:**
  - the closed League menu is `inert`, and scrolls at 1024×768;
  - error pages are titled "Not found" and light no tab;
  - /manager no longer crashes when a Sleeper fetch fails;
  - Records years link to their Seasons page;
  - off-site footer and news links open a new tab.
- **Audit:** 23 pages × 3 widths, all pass.
  - smallest font at least 12px;
  - no horizontal scroll;
  - 44px targets at 375px;
  - layout shift at most 0.05: Standings was 0.60, Home was 0.10.

**Still open (in `site-todo.md`):**
- **[Garrett]** retag 3 previews in Contentful;
- **[Managers]** profile fields and Sleeper team names;
- **Stat Lab second release**;
- **optional lore card**.

Garrett approved the home copy and asked for a direct push to `master` once the go-live checks
pass.

## Round 2 (branch `stat-lab-2`, 2026-10-03; not yet pushed)

### Stat Lab: minimum-games filter and distribution chart (Sonnet)

Commits `8be36cd`, `48ae88d`.

- **Minimum games:**
  - The default is worked out from the view: a third of the most games any row has, capped at
    5 for Seasons and 10 for Careers. Opponent-filtered views use 2/5, capped at 4.
  - It shows how many rows are hidden, and can show them in one tap. It's stored as `min` in the
    address only when it differs from the default.
  - Presets no longer let small samples win:
    - Tucker's 2025 now leads luck;
    - Garrett leads "Who owns whom".
- **Distribution chart (`chart=dist`):**
  - one 44px strip per manager, sorted by median;
  - a fixed beeswarm, so dots never reshuffle;
  - a median tick, and the middle-half band where a manager has 8 or more values;
  - "Boom or bust" now uses it.
  - Checked: Kevin's median, 110.08, matches Node.

### Trophy Room: "From the archives" card (Opus)

Commits `2d497c8`, `ce92d36`.

- **Eight facts:** origins, closest finish, bench record, the 2025 title run, the Hurts keeper,
  the Etienne pick, the biggest blowout, the biggest FAAB bid.
- **All recomputed** from `static/data`, and all fixed through 2025.
- **Stored** in `src/lib/History/archiveFacts.js`.
- **Upkeep:** step 5 of the `CLAUDE.md` end-of-season checklist refreshes them.

The build passes. Paused for Garrett's review before pushing.
