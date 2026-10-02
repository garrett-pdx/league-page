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
| 5 | **D.** Links between pages, plus **History step 2**, the head-to-head grid | Both work on Rivalry and manager links | running (Sonnet); lore-script fix running in parallel (Opus, worktree) |
| 6 | **C4–C5 + B4–B5.** Drafts, remaining small text and tap targets, blog typography, desktop layouts | Polish on less-used pages | pending |
| 7 | **E. Content:** bio typos and league lines (7a, running in parallel in a worktree, Opus); home page copy, Resources, countdown (7b) | Writing, once the page frames are settled | 7a done (merged); 7b pending |
| 8 | **History step 3.** Seasons archive | Biggest new page | pending |
| 9 | **History step 4.** Stat Lab, first release | Built on everything above | pending |
| 10 | **F wrap-up.** `CLAUDE.md` corrections, end-of-season checklist, `mudd-preview` post type, full-site audit | Docs describe the finished state | pending |

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
- Kabroa's "72.1 points left on the bench" was really 54.0.
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
