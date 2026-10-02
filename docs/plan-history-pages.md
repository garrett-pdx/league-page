# Plan: four league-history pages

Drafted 2026-10-02 from the site design review. Four pages:

1. **Schedule luck**: all-play standings, added under the Standings table.
2. **Head-to-head grid**: every manager against every other, all-time, added to Rivalry.
3. **Seasons**: an archive with one page per year at `/seasons/[year]`.
4. **Stat Lab**: a page for filtering, sorting and charting league history.

Everything else from the review is in [`site-todo.md`](site-todo.md).

---

## Why they share one foundation

All four pages are built from the same thing: one row per team per game. Each row says who
played whom, what each side scored, and whether the game was regular season or playoffs.
Today that information only exists inside `weeks.json` (455 KB). It is too big to fetch on a
page and it carries traps that have already produced wrong facts once.

So step 0 is to precompute that game table once, check it, and serve it small. Then every
page computes from the same rows, with the same filters, and the four pages can never
disagree with each other.

## Phase 0: the game table (effort M)

### `scripts/derive-site-data.py`, a new script

It reads `weeks.json`, `league-history.json` and `transactions.json`, and writes two files.

**`static/data/games.json`.** One row per team per game:

```
season, week, user_id, opponent_id, pf, pa, result (W/L/T), kind, max_pf
```

- `kind` is one of `regular`, `playoff`, `consolation` or `placement`.
- `max_pf` is the best lineup the team could have set that week. It is optional; see
  decision 3 below.
- Store it as a column header plus arrays of values, with managers as indexes into a short
  list.
- Expected size: about 700 rows, roughly 30 KB raw and under 10 KB gzipped.

**`static/data/season-notes.json`.** Facts for each season that `league-history.json` lacks:

- that season's trades, with players and picks resolved to names;
- each team's top three scorers, counting starter points only;
- the season's highest and lowest weeks.

Expected size about 20 KB, so the 329 KB `transactions.json` is never shipped to the browser.

### Rules the script must follow

Each of these has already caused a wrong fact in this repo.

- **Ignore week 18.** Rows with `matchup_id == 0` are not real games. Reuse `has_matchup()`
  from `derive-narratives.py`.
- **Ignore unplayed weeks, one week at a time.** 2026 weeks 4–18 have real pairings and every
  score at 0.0. `season_played()` only checks a whole season, so a week counts only when it is
  complete: the season is finished, or the week is before the current NFL week.
- **Work out playoff `kind` from the brackets, not the week number.** Bracket rows use
  roster IDs, so map them through `managers[uid].records[season].roster_id` for that season.
- **Key everything on `user_id`.**

### Self-checks: the script exits non-zero if any fail

- Each manager's wins, losses and points for in each season match
  `league-history.json → managers.*.records` exactly.
- If `max_pf` is included, each season's total agrees with Sleeper's `potential_points` to
  within 1%.
- Every regular-season week has exactly five games, and every game appears twice, once from
  each side.

### Wiring it in

- Add `"derive-site-data"` to `package.json`.
- Add it to the `mudd-data` skill's refresh step, after `pull-league-history.py`. That skill
  already runs twice a week for the blog, so the files stay current in season. Pages show a
  "data through week N" stamp.
- Fix the related bug in `pull-league-history.py`: `seasons.2026.weeks_played` lists weeks
  1–18, though only weeks 1–3 have been played.

### Browser code (new files)

- **`helperFunctions/leagueGames.js`.** Fetches and caches `games.json` the same way
  `leagueHistory.js` already does: SSR-safe and never caching a failed fetch. It also holds
  the pure functions every page uses: `filterGames()`, `allPlay()`, `headToHead()` and
  `standingsFrom()`.
- **`liveSeasonGames()`.** Builds the same row shape from Sleeper's live
  `getLeagueMatchups()`. The Standings page uses it so its luck numbers can never lag the live
  table next to them.

## Page 1: Schedule luck on Standings (effort S)

**What it shows.** For each team this season:

- **All-play record:** how the team would stand if it played all nine others every week.
- **All-play %.**
- **Expected wins:** all-play % × games played.
- **Luck:** actual wins minus expected wins, shown as +/−.

Above the table, one sentence explains it in the league's voice.

**Data.** This season comes from `liveSeasonGames()`, counting completed weeks only.

**Where it goes.**
- A new `src/lib/History/AllPlayTable.svelte`, under its own "Schedule luck" `SectionHeading`.
- It is mounted in `src/routes/standings/+page.svelte`, not inside upstream's
  `Standings/index.svelte`, which keeps the merge risk to one line.
- In the preseason it shows last season's luck from `games.json`, alongside the existing
  last-season table.

**Mobile.** Four tight columns: team, all-play record, expected wins, luck. Luck uses a sign
and a short bar, not colour alone.

**Reuse.** The same component goes on each Seasons page.

**Checks.**
- Every team's all-play wins plus losses equals 9 × weeks played.
- The luck column sums to roughly zero across the league.

## Page 2: Head-to-head grid on Rivalry (effort S)

**What it shows.**
- An 11×11 grid. Each cell is the row manager's record against the column manager.
- A totals column at the end. The diagonal is blank.
- A Regular / Playoffs / All toggle, using the existing `SegmentedControl`.
- Each cell shades from losing to winning, and the record is always printed in it, so colour
  is never the only signal.
- Jordan Leonard is included, dimmed and marked as Moratorium.
- Tapping a cell opens `/rivalry?player_one=…&player_two=…`, the page's existing detailed
  comparison. Check which ID those parameters take when building.

**Where it goes.**
- A new `src/lib/History/HeadToHeadGrid.svelte`, mounted at the top of
  `src/routes/rivalry/+page.svelte`.
- Its heading tells you to pick a cell, or the dropdowns below, for the full rivalry.

**Mobile.** An 11-column grid doesn't fit at 375px. Below 768px it switches to a manager
picker, then a list of that manager's opponents with record bars, sorted.

**Checks.**
- Three or four pairings match what the Rivalry page already shows for them.
- Each row's total equals that manager's career record in `league-history.json`, counting
  regular season only.

## Page 3: Seasons archive (effort M–L)

**Routes.**
- `/seasons`: a card for each season showing the champion, runner-up, top seed, and that
  season's best single week.
- `/seasons/[year]`: one page per year.
- Both live under a new `src/routes/seasons/` directory.

**Each year's page, top to bottom:**

1. **Header.** Champion and title-game result, with the Trophy Room ribbon art.
2. **Final standings, 1–10.** From `final_standings`, with regular-season record, points for
   and points against, plus that season's all-play and luck columns (reusing Page 1's table).
3. **Playoff bracket.** A small read-only view: four teams, two rounds, placement games. It
   is built new from `brackets` rather than forcing upstream's live `Brackets.svelte`, which
   expects Sleeper's live data shapes.
4. **Standings by week.** A chart of each team's rank week by week, with one team highlighted
   on tap. This is the most "story of the season" view.
5. **Draft and keepers.**
   - The first three rounds plus every keeper with its cost, from the `primary` draft.
   - The 2022 page shows only the primary draft, never the carried-over one.
   - A link goes to `/drafts` for the full board.
6. **Trades.** From `season-notes.json`.
7. **Season extremes.** Highest and lowest weeks, biggest blowout, closest game, and each
   team's MVP.

**Edge cases.**
- **2026:** labelled "in progress". It shows standings so far and links to Standings and
  Matchups. It has no final table, because `final_standings` correctly leaves it out.
- **2021 (ESPN):** an honest short page with the founding story and the carried-over draft.
  No standings exist for it, and the page says so.

**Links in.**
- Trophy Room's year headings.
- Manager pages' career band: each finish links to that season.
- Records entries, which link to the season they come from.

**Checks.**
- Every champion and full 1–10 finish matches `league-history.json`.
- The 2022 keepers match `keepers.json` (18 of them).

## Page 4: Stat Lab (effort L)

A page for poking at league history: pick what to look at, filter it, sort it, and see it
charted.

**Data.** `games.json` and `league-history.json` only, so every number agrees with the other
three pages.

**What you can look at:**

| Dataset | One row is | Example questions |
| --- | --- | --- |
| Games | one team's score in one week | highest-scoring weeks; every 2024 blowout |
| Seasons | one manager's season | luckiest seasons ever; points for vs. points against |
| Managers | one career | win %, average points, consistency, titles |
| Matchups | one pairing of managers | who owns whom; highest-scoring rivalries |

**Controls:**
- **Filters:** seasons (multi-select), managers (multi-select), game type
  (regular / playoffs / all), week range, opponent.
- **Measure:** points for, points against, margin, win %, all-play %, luck, consistency
  (spread of weekly scores), plus max points and bench points if decision 3 allows them.
- **Chart:**
  - **Bar:** a ranking.
  - **Line:** over weeks or seasons.
  - **Scatter:** two measures against each other, such as points for vs. against, which
    gives a lucky/unlucky quadrant.
  - **Distribution:** every weekly score per manager, which shows boom/bust at a glance.
- **Table:** always under the chart, showing the same rows. Click any heading to sort.
  - The rank is recomputed after sorting, so the problem that ruled out sorting on Records
    doesn't apply here.
  - Clicking a bar, point or row narrows the filters to it: a manager to that manager, a game
    to that week.
- **Link to the current view.** Every control is stored in the page address, so a blog post
  or group chat can link to a specific chart.
- **Presets** to start from:
  - Luckiest seasons
  - Biggest weeks ever
  - Points for vs. against, this season
  - Boom or bust
  - Who owns whom

**Mobile.**
- The controls fold into a filter sheet, shown as a row of summary chips at the top.
- The chart runs full width, with tap-to-inspect instead of hover.
- The table shows three columns, and tapping a row expands the rest.

**How it's built.**
- A new `src/routes/stat-lab/` route and a `src/lib/StatLab/` directory.
- Charts are hand-written SVG Svelte components using the theme tokens, perhaps with
  `d3-scale`. There is no charting library in the repo today and the data is small, so a heavy
  dependency isn't worth it.
- Load the `dataviz` skill before writing the chart code.

**Ship in two steps.**
1. **First release:** Games and Seasons, bar/line/scatter charts, filters, saving the view in
   the page address, and the presets.
2. **Second release:** Managers and Matchups datasets, distribution charts, and possibly
   player-level data. That would need a new player-season file with its own size budget, so
   it is not in this plan.

## Order of work

Each step is its own commit, checked in the browser at phone and desktop sizes before it goes
to `master`.

| # | Step | Effort | Why this order |
| --- | --- | --- | --- |
| 0 | Game table: script, checks, loader | M | Everything depends on it |
| 1 | Schedule luck on Standings | S | Most useful right now, mid-season |
| 2 | Head-to-head grid | S | Cheap, and feeds the weekly preview |
| 3 | Seasons archive | M–L | Biggest gap; most useful in the offseason |
| 4 | Stat Lab, first release | L | Built on everything above |

**Keeping upstream merges easy.**
- Almost everything is in new files: `src/lib/History/`, `src/lib/StatLab/`,
  `src/routes/seasons/`, `src/routes/stat-lab/`, the new helper, and the new script.
- Upstream files gain one line each: the Standings and Rivalry route files, and `tabs.js`.

## Decisions for you

1. **Where Seasons and Stat Lab go in the nav.** The "League Info" dropdown already has 10
   items. Recommendation: first do the nav regroup from the to-do list (This Season /
   History / Rules & Tools), and put both new pages under History.
2. **The name "Stat Lab".** Alternatives: "Film Room" (more football, less obvious) or
   "Explorer". The review found that unclear labels were the site's main problem, so the
   recommendation is a plain name.
3. **Bench and max-points measures.** Records' Lineup IQ uses Sleeper's season
   `potential_points`. A per-week figure computed by the script could differ slightly.
   Recommendation: include it only if the self-check against Sleeper holds within 1%, and label
   it "max possible" so it never claims to be Sleeper's number.
4. **Current-season freshness.** The grid and Stat Lab read `games.json`, refreshed twice a
   week, while Standings is live. Recommendation: accept the lag and show "through week N".
   The alternative, merging live data on every page, is a lot more work for little gain.
