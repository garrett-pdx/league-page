# Site to-do list

From the design review of 2026-10-02. The four new pages (schedule luck, head-to-head grid,
Seasons, Stat Lab) are planned separately in [`plan-history-pages.md`](plan-history-pages.md).
This list is everything else.

**Who acts:**
- **[Garrett]** needs your decision or access.
- **[Managers]** needs another manager.
- Everything without a tag can be done from the code and data already here.

**Merge risk:**
- **(upstream)** edits a file shared with nmelhado/league-page, so expect merge conflicts.
- **(ours)** stays in config or league-specific files.

## Still open (2026-10-03, after the revamp)

Everything ticked below landed on the `site-revamp` branch; `docs/revamp-log.md` has the
detail. What is left:

- [x] **[Garrett] Approve the home page copy** (`homepageText` in `leagueInfo.js`). Approved
  2026-10-03.
- [ ] **[Garrett] Retag the three previews in Contentful** from `Recap` to `Preview`: Week 2
  (`5XKBEmMeWJrgt0JTjcEA2R`), Week 3 (`6XqfrUTwqZHqXDJpzPF3Xo`) and Week 4
  (`7pgFzp2SPXlyLa10gexnEJ`). Republishing each with the `mudd-preview` skill's command
  does the same. Until then the blog's Recap filter mixes them in.
- [ ] **[Managers] Profile fields and team names** — see the two items under Content. The
  ask is written out in `plan-site-todo.md` ("Asks for other managers").
- [ ] **Stat Lab, second release:** a matchups dataset and head-to-head grid, a distribution
  (boom or bust) chart, a minimum-games control, and keyboard focus for line and scatter
  points.
- [ ] **League lore on the site** (optional) — see the item under Content.
- [ ] **Small, from the step-10 audit, all mouse-only desktop sizes that the 12px / 44px rule
  doesn't cover:** the Free Agents depth-slot buttons are 26px tall above 700px, and the
  constitution's table-of-contents buttons 29–31px. Both are 44px on phones.
- [x] ~~Records entries linking to their season~~ — done in step 10 (`b742fcc`): every
  record's year, and a season page link on each single-season view.

## Do first

- [x] **Update for the 2026 roster change.** Sleeper's 2026 league has **5 bench spots** (2025
  had 6), and the 2026 draft was **13 rounds** (2023–25 were 14). Garrett confirmed it was
  **voted on, 7–3**. Update:
  - `src/routes/constitution/+page.svelte:347`: six bench / fourteen roster spots → five / thirteen
  - `src/routes/constitution/+page.svelte:418`: fourteen-round draft → thirteen
  - `src/lib/utils/leagueInfo.js:45`: "six on the bench" in `homepageText`
  - stale mentions of "14" in `src/routes/CLAUDE.md:55`, `src/lib/utils/CLAUDE.md:83`, and a
    comment at `src/lib/Drafts/Draft.svelte:63`
  → Done in step 1 (`90148b4`): constitution, `homepageText`, the CLAUDE files and the `Draft.svelte` comment; the constitution notes the 7–3 vote.
- [x] **[Garrett] Review two bios that are public under real names.**
  - Tucker Harris's bio (`leagueInfo.js:129`) has a "young boys" line, added in `fe9df6d`. On a
    search-indexed page it reads as an abuse insinuation, even if it's an inside joke.
  - Kevin's "420/69/666" stats are presented as fact.
  → Decided 2026-10-02: leave both as they are.
- [x] **Regroup the nav.** (ours, plus a small change to NavLarge, which already differs from
  upstream.) The new History pages need somewhere to go.
  - Promote **Free Agents** to the top bar.
  - Rename **League Info** to **League**, with three labelled groups:
    - **This Season:** Rosters
    - **History:** Trophy Room, Records, Rivalry, Drafts, and later Seasons and Stat Lab
    - **Rules & Tools:** Constitution, Keeper Draft Board, Resources, Sleeper
  - Mark off-site links with ↗.
  - Drop the Home tab (decided); the seal logo already links home.
  - The one-dropdown limit can stay for now.
  → Done in step 1 (`3e70099`): This Season / History / Rules & Tools, Free Agents promoted, Home dropped, ↗ on off-site links. Seasons and Stat Lab joined History in steps 8–9.

## Navigation and wayfinding

- [x] **Browser tab titles should match the nav labels.** (upstream, one line plus a helper)
  `src/lib/Nav/index.svelte:9` currently capitalises the URL path instead. It should:
  - look the label up in `tabs.js`;
  - use the manager's name on `/manager`, since all 11 manager pages are titled "Manager" now;
  - use the post title on `/blog/[slug]`, instead of "Blog/some-slug".
  → Done in step 1 (`dde3359`): `src/lib/utils/pageTitle.js`. Step 10 added "Not found" for error pages.
- [x] **Nav highlight should follow the current page.** (already differs from upstream) **High:**
  two reviews found it independently. On desktop, Home stays underlined on every page. On
  phones, the menu keeps highlighting the page you landed on. NavLarge (`:10`) and NavSmall
  (`:15`) set the highlight once, when the page first loads; a `$derived` fixes it.
  Make it follow `page.url.pathname`, and highlight the current item inside the dropdown.
  → Done in step 1: `findTab` / `currentDest` in `tabs.js`.
- [x] **Add links between pages:**
  - [x] Manager page → their rivalry page, via `/rivalry?player_one=…&player_two=…`. (ours)
  - [x] Manager page → their matchup this week.
  - [x] Team names on matchup cards and playoff brackets → manager pages
    (`Matchup.svelte`, `BracketsColumn.svelte`). (upstream)
  - [x] Home page NFL week banner → Matchups.
  → Done in step 5 (`e389540`, `c62f72a`, `0c6b971`).
- [x] **Turn clickable `div`s into real links.** That makes them keyboard-reachable and
  openable in a new tab. Found at:
  - `Standing.svelte:32`
  - `Bar.svelte:130`
  - the home page champion panel
  - "( view more )" in `Transactions.svelte:77,93`
  → Done in step 5 (`0c6b971`); helper `$lib/utils/managerLink`.

  (upstream)
- [x] **Home page: add a "Find your way" row** to `homepageText` (ours): this week's matchups ·
  standings · Trophy Room · constitution.
  → Done in step 7b (`3270061`); the copy was approved by Garrett on 2026-10-03.

## Page names and headings

- [x] **Trophy Room** has three names: nav "Trophy Room", tab title "Awards", page heading "Hall
  of Fame". Make the page say "Trophy Room", with Hall of Fame and Awards as sections.
  → Done in step 4: `PageHeader` "Trophy Room", tab title to match.
- [x] **Add a heading and a one-line intro to pages that have none:**
  - Records (`Records/index.svelte:110`). Note the page also holds Rankings.
  - Rosters (`RosterSorter.svelte:121`).
  - Drafts.
  → Done in step 4 (`123301d`): `PageHeader` on every page, mounted in the route files.

  Use the `SectionHeading` pattern from Free Agents and Managers, placed in the route files to
  keep merge risk low.
- [x] **Drafts** leads with a projected 2027 board, while the completed 2026 draft sits under
  "Previous Drafts" (`Drafts/index.svelte:34`, `leagueDrafts.js:37-42`). During the season,
  lead with the draft that actually happened.
  → Done in step 6 (`d9becd2`): the completed draft leads; the projection sits behind a `Disclosure`.
- [x] **Trades & Waivers** is headed "Recent Transactions" but shows every season
  (`TransactionsPage.svelte:259`). Its filter button just says "Both". (upstream)
  → Done in step 4 (`d2b4cf2`): heading from `PageHeader`, the button says "All".
- [x] **Typo:** "Performance Comparisson" → "Comparison" (`Rivalry/index.svelte:222`). Leave the
  `ComparissonBar` filename alone; renaming it would conflict with upstream.
  → Done in step 4.
- [x] **Rivalry dropdowns** show Sleeper handles, while Managers shows real names
  (`ManagerSelectors.svelte:133,149`).
  → Done in step 4; step 5 also filtered out `Football_Team`.
- [x] **Blog:** use "The Mudd Report" as the page heading
  (`Posts.svelte:144`, `HomePost.svelte:82`). Keep the nav label "Blog"; the nav code hides the
  tab by testing for that exact label.
  → Done in step 4.
- [x] **Free Agents:** the intro says "every unrostered player", but the "Show rostered" toggle
  covers everyone (`FreeAgents.svelte:475,484`). Reword the intro.
  → Done in step 4: the intro now mentions Show rostered.

## Content

- [x] **Standings:** remove the three empty division columns and the all-zero ties column
  (`Standings/index.svelte:19,22`). Upstream expects forks to edit these lines.
  → Done in step 2 (`f587e7e`).
- [x] **Bio typos** in `leagueInfo.js`:
  - `:129` "visable", "Acadamey", and "Completed in" (should be "Competed in")
  - `:165` "legand"
  - `:177` a missing "he" before "threw", and "32/59 (74.2%)" where 32/59 is 54.2%. The
    percentage was correct before `fe9df6d`.
  - Leave `:201` "Marvey Mudd" (Malcolm's bio); it reads as a deliberate joke.
  → Done in step 7a (`cea7206`, `99310d2`, `aca77a9`).
- [x] **Add one Mudd League line to each active bio**, taken from `docs/league-lore.md`: career
  MVP, best keeper, longest streak, or perfect lineups. Today every bio is only about college
  football. Re-derive each number when writing it, not from memory.
  → Done in step 7a: every figure re-derived from the data.
- [ ] **[Managers] Collect the optional profile fields:** favourite NFL team, how to reach them,
  trade willingness (1–10), a one-line philosophy, favourite player. All seven fields are unset
  for all 11 managers, so each manager page shows a single Rival tile. Skip `mode` and
  `rookieOrVets`; those are for dynasty leagues.
- [ ] **[Managers] Team names:** kshoyer, tuckersdumbteam and TnT44 have none in Sleeper, so the
  site shows their handles.
- [x] ~~Fill gaps in the constitution~~ (draft order, keeper deadline, tiebreakers and seeding,
  inactive managers). **Dropped:** the league has no rules for these yet, and the site shouldn't
  invent them. If the league ever wants them written down, start from how Sleeper's settings
  already behave and put it to a vote.
- [x] **Resources:** add league-specific links in a new component, so upstream's list stays
  untouched:
  - the Keeper Draft Board, the Sleeper league, the Constitution and the blog;
  - half-PPR rankings, an injury report, and FAAB guides.
  → Done in step 7b (`442c350`): `src/lib/Resources/LeagueLinks.svelte` first, news feed last.

  Move the news feed to the bottom of the page (decided). It returned only five podcast
  episodes.
- [x] **Home page right rail:** the countdown hides once the draft is done. Reuse `Countdown`
  to count down to the trade deadline (week 12), then to the playoffs.
  → Done in step 7b (`fd916f8`): `src/lib/Home/SeasonMilestone.svelte`, "N weeks away" with no ticking clock, because Sleeper publishes no lock time for the deadline.
- [x] **[Garrett] Blog post types:** previews publish as type "Recap", so the blog's category
  filter mixes them in. Pass `--type Preview` in the `mudd-preview` skill and retag the three
  existing previews in Contentful.
  → Skill half done in step 10 (`47b8c47`): `mudd-preview` passes `--type Preview`; no code or Contentful model change was needed. The retag is still open (see Still open).
- [ ] **League lore:** most of the 294 facts in `narratives.json` never appear on the site
  (streaks, bench disasters, best and worst keepers, draft steals, FAAB splurges, luck). Some
  can go on the Seasons pages; consider a hand-picked lore card on Trophy Room as well.
  Don't fetch the full 97 KB file at runtime.

## After the season (add to the checklist)

- [x] Update the hand-written champion lines: `homepageText` (`leagueInfo.js:47`) and Malcolm's
  bio (`:201`). Better: delete the homepage paragraph, since the right-rail champion panel
  updates itself.
  → Homepage paragraph deleted in step 7b. Malcolm's "Reigning champion." is item 4 of the end-of-season checklist in `CLAUDE.md`.
- [x] Re-run `pull-league-history.py`, `derive-narratives`, and the new `derive-site-data`.
  → Item 1 of the end-of-season checklist in `CLAUDE.md` ("The data pipeline").

## Data and documentation

- [x] `pull-league-history.py`: for the season in progress, `weeks_played` lists unplayed weeks
  (2026 shows weeks 1–18), and ownership spans run to week 18. Count a week only once points
  have been scored in it. This is also step 0 of the History pages plan.
  → Done in History step 0 (`7acaf69`): completed weeks only, `nfl_state` recorded.
- [x] **Correct `CLAUDE.md`:**
  - unset manager fields are hidden, not shown as "?";
  - rival is no longer "The Field" for everyone;
  - the Conventions section still says the blog is off;
  - BBrown16's team name is out of date;
  - `narratives.json` has 294 facts, not 278 (after the lore fix);
  - the 14-round and 6-bench mentions, once the roster change is confirmed.
  → Done in step 10.

## Phone and desktop

Tested on the live site at 375px, 1024px and 1440px. The nav highlight bug, the standings
columns and the missing headings were also found by the other reviews; they are listed above.

**Merge risk here has three levels:**
- **(upstream)** the file is identical to upstream, so a change is a guaranteed conflict.
- **(changed)** an upstream file this fork has already modified.
- **(ours)** a league-owned file.

### High

- [x] **Stop shrinking text to fit on phones.** Text drops as low as 5–8px.
  - **Records:** table cells are 8.4px, and seven filter buttons wrap onto two rows with 6.4px
    labels. The rules are `:global`, so they also shrink Matchups.
    Files: `RecordsAndRankings.svelte:454-531`, `Records/index.svelte:84-104` (changed);
    `PerSeasonRecords.svelte:136-143` (upstream).
  - **Matchups:** team names are 5.6px and projections 7.8px. The Regular Season / Playoffs
    toggle label is 6.4px. Files: `Matchup.svelte:323,338-375` (upstream).
  - **Drafts:** the KEEPER tag is 5.4px.
  - **Fix:** set a 12px minimum, and replace the SMUI button groups with the existing
    `SegmentedControl`.
  → Done in steps 2 and 6: 12px floor on every page at 375px; `SegmentedControl` replaced the button groups.
- [x] **Standings table on phones.** It is 708px wide in a 375px screen. Make the Team column
  sticky, in addition to removing the empty columns listed under Content. That brings it to
  about 430px.
  → Done in step 2: columns dropped, Team pinned, no page scroll.
- [x] **Drafts on phones.** The empty upcoming board comes first: a 1200px grid in a 354px box
  that also scrolls vertically, which pushes the real drafts far down. Put past drafts first,
  and fix the typo "Upcomig". Files: `Drafts/index.svelte:25-36` (upstream),
  `Draft.svelte:112,180` (changed).
  → Done in step 6 (`d9becd2`).

### Medium

- [x] **The page jumps as data loads.** The footer starts on screen and gets pushed down.
  Layout shift scores 0.62 on /manager and 0.44 on /standings; anything over 0.25 rates
  "poor". Fix: add `min-height: 100vh` to the page wrapper, or reserve height on the
  `.loading` blocks, in a league-owned global style. Files: `Footer.svelte:79`,
  `routes/+layout.svelte:10`.
  → Done in step 4 (`78437cd`), CSS only in `_site.scss`: /standings 0.78 → 0.02, /manager 0.66 → 0.
- [x] **Home page on phones.** About 900px of rules text comes first: power rankings start at
  y≈1810 and the champion at y≈2500. The blog preview cuts off mid-heading. Fix: tighten
  `homepageText`, or move the rules detail to the Constitution and link to it. (ours)
  → Done in step 7b: a phone order that puts power rankings at y≈930.
- [x] **One page heading style everywhere.** Only Managers, Hall of Fame and Free Agents use
  `SectionHeading`.
  - Standings, Blog, Rivalry, Resources, Records and Drafts use plain black headings.
  - The Awards year headings are grey.
  - The Constitution heading is all caps.
  → Done in step 4 (`PageHeader`).
- [x] **Blog posts.**
  - Headings sit on a 60px line height, so a two-line heading reads like three. Set
    `line-height: 1.15` (`FullPost.svelte:92ff`).
  - Body lines run about 140 characters on desktop. Cap them at `--pageMaxText`
    (`routes/blog/[slug]/+page.svelte:15`).
  - Card titles run flush to the card edge.
  - Tables sit flush left while the text is indented.
  → Done in step 6 (`0676eb4`), checked against a mock because the blog can't run locally without a delivery token.
- [x] **Manager page.**
  - **Phones:** 8.6–9.6px chip and caption text, and the bio header wraps awkwardly.
  - **Desktop:** it looks like a stretched phone page. Use two columns (bio | roster) above
    1100px.
  - Files: `Manager.svelte:121-122`, `ManagerAwards.svelte` (changed).
  → Done in step 6 (`63dcfec`): 12px floor, two columns above 1100px.
- [x] **Awards (Trophy Room).**
  - On phones, podium name labels overlap the avatars.
  - The page is 7,200px tall.
  - Files: `Awards.svelte:159-175,262,267-361,372` (changed).
  → Done in step 6 (`835bb53`): names under the podium on phones, earlier seasons folded (6,688px → 3,160px).
- [x] **Rosters:** add a team jump list, since the page is 6,350px tall.
  → Done in step 6 (`c25d2e2`): `TeamChips`.

### Mobile nav

- [x] **Make the hamburger button accessible.** It is an `<i>` with no role or label, so a
  keyboard can't reach it. It is grey (#888) (`NavSmall.svelte:47-55,85`).
  → Done in step 1 (`10c39c5`).
- [x] **Keep the nav at the top on long pages,** or add a back-to-top button. Pages run
  5,000–7,000px tall (`Nav/index.svelte:17-23`).
  → Done in step 1: sticky 61px bar on phones (`--stickyBar`).
- [x] **Fix menu text contrast.** Unselected items are #858585 on white, about 3.7:1, which
  fails AA.
  → Done in step 1: 7.46:1.
- [x] **Make menu items 44px tall;** they are 40px now. The last item falls below the fold.
  → Done in step 1.
- [x] **Mark off-site links** (Sleeper, the Draft Board) as opening elsewhere. This is shared
  with the nav regroup above.
  → Done in step 1.

### Low

- [x] Small tap targets:
  - Transactions pagination arrows are 24px.
  - Rivalry dropdowns are 30px tall, and both have `id="managerOne"`
    (`ManagerSelectors.svelte:130,146`).
  - Resources podcast links are 19px tall.
  → Done in step 6 (`7738330`).
- [x] Constitution: about 200px of empty space above the title on phones, and a narrow
  left-aligned column on desktop (`routes/constitution/+page.svelte:51,58`).
  → Done in step 4.
- [x] Desktop: the Matchups list is about 530px wide in a 1440px page.
  → Done in step 6 (`6d12cfd`): two columns above 1200px.

**Pages already in good shape:** Free Agents, which the others should be brought in line
with, and Managers.
