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

## Do first

- [ ] **Update for the 2026 roster change.** Sleeper's 2026 league has **5 bench spots** (2025
  had 6), and the 2026 draft was **13 rounds** (2023–25 were 14). Garrett confirmed it was
  **voted on, 7–3**. Update:
  - `src/routes/constitution/+page.svelte:347`: six bench / fourteen roster spots → five / thirteen
  - `src/routes/constitution/+page.svelte:418`: fourteen-round draft → thirteen
  - `src/lib/utils/leagueInfo.js:45`: "six on the bench" in `homepageText`
  - stale mentions of "14" in `src/routes/CLAUDE.md:55`, `src/lib/utils/CLAUDE.md:83`, and a
    comment at `src/lib/Drafts/Draft.svelte:63`
- [ ] **[Garrett] Review two bios that are public under real names.**
  - Tucker Harris's bio (`leagueInfo.js:129`) has a "young boys" line, added in `fe9df6d`. On a
    search-indexed page it reads as an abuse insinuation, even if it's an inside joke.
  - Kevin's "420/69/666" stats are presented as fact.
- [ ] **Regroup the nav.** (ours, plus a small change to NavLarge, which already differs from
  upstream.) The new History pages need somewhere to go.
  - Promote **Free Agents** to the top bar.
  - Rename **League Info** to **League**, with three labelled groups:
    - **This Season:** Rosters
    - **History:** Trophy Room, Records, Rivalry, Drafts, and later Seasons and Stat Lab
    - **Rules & Tools:** Constitution, Keeper Draft Board, Resources, Sleeper
  - Mark off-site links with ↗.
  - Drop the Home tab (decided); the seal logo already links home.
  - The one-dropdown limit can stay for now.

## Navigation and wayfinding

- [ ] **Browser tab titles should match the nav labels.** (upstream, one line plus a helper)
  `src/lib/Nav/index.svelte:9` currently capitalises the URL path instead. It should:
  - look the label up in `tabs.js`;
  - use the manager's name on `/manager`, since all 11 manager pages are titled "Manager" now;
  - use the post title on `/blog/[slug]`, instead of "Blog/some-slug".
- [ ] **Nav highlight should follow the current page.** (already differs from upstream) **High:**
  two reviews found it independently. On desktop, Home stays underlined on every page. On
  phones, the menu keeps highlighting the page you landed on. NavLarge (`:10`) and NavSmall
  (`:15`) set the highlight once, when the page first loads; a `$derived` fixes it.
  Make it follow `page.url.pathname`, and highlight the current item inside the dropdown.
- [ ] **Add links between pages:**
  - [ ] Manager page → their rivalry page, via `/rivalry?player_one=…&player_two=…`. (ours)
  - [ ] Manager page → their matchup this week.
  - [ ] Team names on matchup cards and playoff brackets → manager pages
    (`Matchup.svelte`, `BracketsColumn.svelte`). (upstream)
  - [ ] Home page NFL week banner → Matchups.
- [ ] **Turn clickable `div`s into real links.** That makes them keyboard-reachable and
  openable in a new tab. Found at:
  - `Standing.svelte:32`
  - `Bar.svelte:130`
  - the home page champion panel
  - "( view more )" in `Transactions.svelte:77,93`

  (upstream)
- [ ] **Home page: add a "Find your way" row** to `homepageText` (ours): this week's matchups ·
  standings · Trophy Room · constitution.

## Page names and headings

- [ ] **Trophy Room** has three names: nav "Trophy Room", tab title "Awards", page heading "Hall
  of Fame". Make the page say "Trophy Room", with Hall of Fame and Awards as sections.
- [ ] **Add a heading and a one-line intro to pages that have none:**
  - Records (`Records/index.svelte:110`). Note the page also holds Rankings.
  - Rosters (`RosterSorter.svelte:121`).
  - Drafts.

  Use the `SectionHeading` pattern from Free Agents and Managers, placed in the route files to
  keep merge risk low.
- [ ] **Drafts** leads with a projected 2027 board, while the completed 2026 draft sits under
  "Previous Drafts" (`Drafts/index.svelte:34`, `leagueDrafts.js:37-42`). During the season,
  lead with the draft that actually happened.
- [ ] **Trades & Waivers** is headed "Recent Transactions" but shows every season
  (`TransactionsPage.svelte:259`). Its filter button just says "Both". (upstream)
- [ ] **Typo:** "Performance Comparisson" → "Comparison" (`Rivalry/index.svelte:222`). Leave the
  `ComparissonBar` filename alone; renaming it would conflict with upstream.
- [ ] **Rivalry dropdowns** show Sleeper handles, while Managers shows real names
  (`ManagerSelectors.svelte:133,149`).
- [ ] **Blog:** use "The Mudd Report" as the page heading
  (`Posts.svelte:144`, `HomePost.svelte:82`). Keep the nav label "Blog"; the nav code hides the
  tab by testing for that exact label.
- [ ] **Free Agents:** the intro says "every unrostered player", but the "Show rostered" toggle
  covers everyone (`FreeAgents.svelte:475,484`). Reword the intro.

## Content

- [ ] **Standings:** remove the three empty division columns and the all-zero ties column
  (`Standings/index.svelte:19,22`). Upstream expects forks to edit these lines.
- [ ] **Bio typos** in `leagueInfo.js`:
  - `:129` "visable", "Acadamey", and "Completed in" (should be "Competed in")
  - `:165` "legand"
  - `:177` a missing "he" before "threw", and "32/59 (74.2%)" where 32/59 is 54.2%. The
    percentage was correct before `fe9df6d`.
  - Leave `:201` "Marvey Mudd" (Malcolm's bio); it reads as a deliberate joke.
- [ ] **Add one Mudd League line to each active bio**, taken from `docs/league-lore.md`: career
  MVP, best keeper, longest streak, or perfect lineups. Today every bio is only about college
  football. Re-derive each number when writing it, not from memory.
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
- [ ] **Resources:** add league-specific links in a new component, so upstream's list stays
  untouched:
  - the Keeper Draft Board, the Sleeper league, the Constitution and the blog;
  - half-PPR rankings, an injury report, and FAAB guides.

  Move the news feed to the bottom of the page (decided). It returned only five podcast
  episodes.
- [ ] **Home page right rail:** the countdown hides once the draft is done. Reuse `Countdown`
  to count down to the trade deadline (week 12), then to the playoffs.
- [ ] **[Garrett] Blog post types:** previews publish as type "Recap", so the blog's category
  filter mixes them in. Pass `--type Preview` in the `mudd-preview` skill and retag the three
  existing previews in Contentful.
- [ ] **League lore:** most of the 302 facts in `narratives.json` never appear on the site
  (streaks, bench disasters, best and worst keepers, draft steals, FAAB splurges, luck). Some
  can go on the Seasons pages; consider a hand-picked lore card on Trophy Room as well.
  Don't fetch the full 97 KB file at runtime.

## After the season (add to the checklist)

- [ ] Update the hand-written champion lines: `homepageText` (`leagueInfo.js:47`) and Malcolm's
  bio (`:201`). Better: delete the homepage paragraph, since the right-rail champion panel
  updates itself.
- [ ] Re-run `pull-league-history.py`, `derive-narratives`, and the new `derive-site-data`.

## Data and documentation

- [ ] `pull-league-history.py`: for the season in progress, `weeks_played` lists unplayed weeks
  (2026 shows weeks 1–18), and ownership spans run to week 18. Count a week only once points
  have been scored in it. This is also step 0 of the History pages plan.
- [ ] **Correct `CLAUDE.md`:**
  - unset manager fields are hidden, not shown as "?";
  - rival is no longer "The Field" for everyone;
  - the Conventions section still says the blog is off;
  - BBrown16's team name is out of date;
  - `narratives.json` has 302 facts, not 278;
  - the 14-round and 6-bench mentions, once the roster change is confirmed.

## Phone and desktop

Tested on the live site at 375px, 1024px and 1440px. The nav highlight bug, the standings
columns and the missing headings were also found by the other reviews; they are listed above.

**Merge risk here has three levels:**
- **(upstream)** the file is identical to upstream, so a change is a guaranteed conflict.
- **(changed)** an upstream file this fork has already modified.
- **(ours)** a league-owned file.

### High

- [ ] **Stop shrinking text to fit on phones.** Text drops as low as 5–8px.
  - **Records:** table cells are 8.4px, and seven filter buttons wrap onto two rows with 6.4px
    labels. The rules are `:global`, so they also shrink Matchups.
    Files: `RecordsAndRankings.svelte:454-531`, `Records/index.svelte:84-104` (changed);
    `PerSeasonRecords.svelte:136-143` (upstream).
  - **Matchups:** team names are 5.6px and projections 7.8px. The Regular Season / Playoffs
    toggle label is 6.4px. Files: `Matchup.svelte:323,338-375` (upstream).
  - **Drafts:** the KEEPER tag is 5.4px.
  - **Fix:** set a 12px minimum, and replace the SMUI button groups with the existing
    `SegmentedControl`.
- [ ] **Standings table on phones.** It is 708px wide in a 375px screen. Make the Team column
  sticky, in addition to removing the empty columns listed under Content. That brings it to
  about 430px.
- [ ] **Drafts on phones.** The empty upcoming board comes first: a 1200px grid in a 354px box
  that also scrolls vertically, which pushes the real drafts far down. Put past drafts first,
  and fix the typo "Upcomig". Files: `Drafts/index.svelte:25-36` (upstream),
  `Draft.svelte:112,180` (changed).

### Medium

- [ ] **The page jumps as data loads.** The footer starts on screen and gets pushed down.
  Layout shift scores 0.62 on /manager and 0.44 on /standings; anything over 0.25 rates
  "poor". Fix: add `min-height: 100vh` to the page wrapper, or reserve height on the
  `.loading` blocks, in a league-owned global style. Files: `Footer.svelte:79`,
  `routes/+layout.svelte:10`.
- [ ] **Home page on phones.** About 900px of rules text comes first: power rankings start at
  y≈1810 and the champion at y≈2500. The blog preview cuts off mid-heading. Fix: tighten
  `homepageText`, or move the rules detail to the Constitution and link to it. (ours)
- [ ] **One page heading style everywhere.** Only Managers, Hall of Fame and Free Agents use
  `SectionHeading`.
  - Standings, Blog, Rivalry, Resources, Records and Drafts use plain black headings.
  - The Awards year headings are grey.
  - The Constitution heading is all caps.
- [ ] **Blog posts.**
  - Headings sit on a 60px line height, so a two-line heading reads like three. Set
    `line-height: 1.15` (`FullPost.svelte:92ff`).
  - Body lines run about 140 characters on desktop. Cap them at `--pageMaxText`
    (`routes/blog/[slug]/+page.svelte:15`).
  - Card titles run flush to the card edge.
  - Tables sit flush left while the text is indented.
- [ ] **Manager page.**
  - **Phones:** 8.6–9.6px chip and caption text, and the bio header wraps awkwardly.
  - **Desktop:** it looks like a stretched phone page. Use two columns (bio | roster) above
    1100px.
  - Files: `Manager.svelte:121-122`, `ManagerAwards.svelte` (changed).
- [ ] **Awards (Trophy Room).**
  - On phones, podium name labels overlap the avatars.
  - The page is 7,200px tall.
  - Files: `Awards.svelte:159-175,262,267-361,372` (changed).
- [ ] **Rosters:** add a team jump list, since the page is 6,350px tall.

### Mobile nav

- [ ] **Make the hamburger button accessible.** It is an `<i>` with no role or label, so a
  keyboard can't reach it. It is grey (#888) (`NavSmall.svelte:47-55,85`).
- [ ] **Keep the nav at the top on long pages,** or add a back-to-top button. Pages run
  5,000–7,000px tall (`Nav/index.svelte:17-23`).
- [ ] **Fix menu text contrast.** Unselected items are #858585 on white, about 3.7:1, which
  fails AA.
- [ ] **Make menu items 44px tall;** they are 40px now. The last item falls below the fold.
- [ ] **Mark off-site links** (Sleeper, the Draft Board) as opening elsewhere. This is shared
  with the nav regroup above.

### Low

- [ ] Small tap targets:
  - Transactions pagination arrows are 24px.
  - Rivalry dropdowns are 30px tall, and both have `id="managerOne"`
    (`ManagerSelectors.svelte:130,146`).
  - Resources podcast links are 19px tall.
- [ ] Constitution: about 200px of empty space above the title on phones, and a narrow
  left-aligned column on desktop (`routes/constitution/+page.svelte:51,58`).
- [ ] Desktop: the Matchups list is about 530px wide in a 1440px page.

**Pages already in good shape:** Free Agents, which the others should be brought in line
with, and Managers.
