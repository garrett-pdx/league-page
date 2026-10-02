# Plan: working through the site to-do list

Drafted 2026-10-02. This turns [`site-todo.md`](site-todo.md) into six workstreams, A–F. Each
one is a commit, or a short series of commits, that can be checked and shipped on its own. The
four new pages are planned separately in [`plan-history-pages.md`](plan-history-pages.md); the
order of work at the end covers both plans.

## Rules that apply to every workstream

**Fork merge rules, from `CLAUDE.md`.** Every to-do item is tagged with one of three risks:
- *upstream*: the file is unchanged from upstream, so any edit risks a merge conflict.
- *changed*: an upstream file this fork has already edited.
- *ours*: a league-owned file.

The rules that follow from that:
- Prefer files we own.
- In a *changed* file, edit freely, but don't reformat.
- In an *upstream* file, keep the diff to the lines that need changing. Deleting a block
  merges cleanly unless upstream edits those same lines.

**CSS overrides vs. edits.** A league-owned global stylesheet can override upstream's
`:global(...)` rules without touching their files. It cannot reliably override Svelte's scoped
rules: scoped selectors carry a hash class, so an override would need `!important` or a guess
at the hash. So:
- use the override file for `:global` rules;
- edit directly when the rule is scoped.

**One new global stylesheet: `src/theme/_site.scss`.**
- It is `@use`d from `_tokens.scss`, which `_smui-theme.scss` already loads, so no upstream
  file gains a line.
- It holds layout fixes and overrides of upstream `:global` rules.
- Remember that `npm run dev` does not recompile Sass. Run `npm run smui-theme-light` after
  every edit.

**How each commit gets checked.**
- Open the dev server in the browser at 375px and 1440px, and run the checking snippet at the
  end of this file on every affected page.
- For anything with a build-time effect, run `DOCKER_BUILD=true npx vite build`. Plain
  `npm run build` fails locally on Node 25.

---

## A. The nav (effort M, do first)

**Covers:** the nav regroup, the stale highlight, tab titles, and the mobile menu's
accessibility, contrast, tap targets and position.

**Why first.** It touches every page. Both the layout reviewer and the phone reviewer rated the
stale highlight high. The new Seasons and Stat Lab pages also need somewhere to go.

### A1. Regroup the menu

All of this lives in `tabs.js`, which is ours.

- Add **Free Agents** to the top bar.
- Rename **League Info** to **League**.
- Inside League, add group headings as plain entries with no destination:
  `{ group: 'This Season' }`, `{ group: 'History' }`, `{ group: 'Rules & Tools' }`.
  - The footer already drops entries without a `dest` (`Footer.svelte`, `.filter((link) => link.dest)`),
    so it needs no change.
  - **NavSmall** (changed): show a `Subheader` for group entries. It already does this for the
    nested tab's label.
  - **NavLarge** (changed): show a small caption for group entries.
  - **NavLarge** also needs its dropdown height fixed. It calculates `49 * tabChildren.length`,
    which group rows would throw off. Measure the list's `scrollHeight` instead.
- Mark off-site children (Sleeper, Keeper Draft Board) with a trailing `open_in_new` icon,
  chosen by the same `^https?://` test `navigate()` already uses.
- Update the constraints comment at the top of `tabs.js`.
  - The single-dropdown rule still holds.
  - Group entries are new; document them.
- **Check the width.** That makes eight top-level tabs, and the desktop nav must fit above the
  950px breakpoint (`Nav/index.svelte`).
  - Measure it in the browser.
  - If it doesn't fit, drop the Home tab first, since the seal already links home. The
    alternative is shortening "Trades & Waivers" to "Trades", but that label covers waivers too.

### A2. A highlight that follows the page

- **NavSmall:** `active = $derived(page.url.pathname)`. Also mark the current dropdown item
  with `activated`.
- **NavLarge:** `active` is used with `bind:active` on SMUI's `TabBar`, so it can't be a plain
  `$derived`. Keep it as `$state` and reassign it in an `$effect` keyed on
  `page.url.pathname`.
  - Use the same lookup the first render already uses: a tab matches if its `dest` matches, or
    one of its children's does.
- The `/manager` page should light **Managers**. Treat `/manager` as belonging to `/managers`
  in the lookup.

### A3. Tab titles that match the nav

- `Nav/index.svelte:9` (upstream) builds the title by capitalising the URL path. Replace that
  expression with a call to a small helper in a new file, `src/lib/utils/pageTitle.js`. The
  upstream diff stays one line.
- The helper's order of preference:
  1. `page.data.title`, if the route's `load` provided one;
  2. otherwise the label from `tabs.js`, matched on the path;
  3. otherwise today's behaviour.
- **`/manager`:** `routes/manager/+page.js` returns `title` from
  `managers[index].name`. It already has the index, and the lookup is synchronous, so the page
  keeps its unawaited-promise loading pattern.
- **`/blog/[slug]`:** the post title comes from Contentful, which is async. Turn the slug into
  readable words in `load()`. Exact post titles aren't worth blocking the page for.

### A4. The mobile menu

- **Hamburger button.** Replace the bare `<Icon>` with a real `<button aria-label="Open menu">`
  wrapping the icon. Use `--accentInk` instead of `#888`, and make the hit area at least 44px.
- **Item text.** `.nav-item` uses `#858585`, about 3.7:1 contrast. Switch it to a token that
  reaches at least 4.5:1, such as `--g555`, and check the measured ratio.
- **Item height:** at least 44px.
- **Long pages.** On phones only, make the bar sticky and compact: a smaller seal, around 48px,
  plus the button.
  - Desktop keeps today's non-sticky header. The dropdown's position is measured with
    `getBoundingClientRect`, so a sticky header would need it re-tested.
  - Fallback if sticky misbehaves: a back-to-top button in `Footer.svelte`, which this fork has
    already changed.

**Checks.**
- Visit every page at both widths, and confirm the right tab is lit after clicking through
  in-page links (a Hall of Fame plaque to a manager to Rivalry).
- Confirm the tab titles.
- Check the footer still lists every page.
- Navigate with the keyboard alone: Tab reaches the hamburger, and Enter opens it.

---

## B. Page headers, naming, and desktop layout (effort M)

**Covers:** consistent page headings and intros; the naming fixes (Trophy Room, "Recent
Transactions", "Comparisson", "Upcomig", the Free Agents intro, The Mudd Report); the page
jumping as data loads; blog typography; and the desktop layout fixes.

### B1. A `PageHeader` primitive

- Add `src/lib/Design/PageHeader.svelte` to our design barrel: a title (rendered through
  `SectionHeading`) plus an optional one-line intro.
- Mount it in each **route file**, so upstream components only lose their old heading.
- Draft the intro copy in the league's voice, from `docs/mudd-voice.md`.

| Route | Header | Remove inside the component |
| --- | --- | --- |
| /standings | Standings | heading at `Standings/index.svelte:115` (changed) |
| /records | Records & Rankings | none (it has no heading) |
| /rosters | Rosters | none |
| /drafts | Drafts | the `<h4>` at `Drafts/index.svelte:34` (upstream) |
| /awards | Trophy Room | keep "Hall of Fame" and "{year} Awards" as section headings, both styled with `SectionHeading` |
| /rivalry | Rivalry | `Rivalry/index.svelte:173` (upstream) |
| /transactions | Trades & Waivers | "Recent Transactions" at `TransactionsPage.svelte:259` |
| /blog | The Mudd Report | `Posts.svelte:144`; nav label stays "Blog" |
| /resources | Resources | the two `<h4>`s, which become sections |
| /constitution | keep as is, but remove the ~200px gap above and centre the column (`+page.svelte:51,58`, ours) | none |

- The new pages from the History plan use the same header from day one.

### B2. Small text fixes

- `Rivalry/index.svelte:222` "Comparisson" → "Comparison". Don't rename `ComparissonBar`.
- `Drafts` "Upcomig" → "Upcoming".
- `TransactionsPage`: the button labelled "Both" → "All".
- Free Agents intro (`FreeAgents.svelte:475`, ours): reword so it covers the "Show rostered"
  toggle.
- `HomePost.svelte:82`: "League Blog" → "The Mudd Report".
- Rivalry dropdowns show real names, not Sleeper handles (`ManagerSelectors.svelte:133,149`).
  Take the name from `managers` and fall back to the handle. Also fix the duplicate
  `id="managerOne"`.

### B3. Stop the page jumping as it loads

- The footer is absolutely positioned at the bottom of `<main>`, which has no minimum height. It
  starts on screen and gets pushed down as data arrives (layout shift 0.44–0.62).
- In `_site.scss`, give `main` `position: relative; min-height: 100vh`, plus bottom padding
  equal to the footer height in place of the current spacer. Read `Footer.svelte:79` and the
  spacer logic first, so the two don't double up.
- Target: layout shift under 0.1 on /manager, /standings and /.

### B4. Blog typography

In `FullPost.svelte` and `routes/blog/[slug]/+page.svelte` (both changed):
- Post headings get `line-height: 1.15`.
- Body text is capped at `--pageMaxText`.
- Tables are indented to match the text.
- Card titles get proper padding.

### B5. Desktop layouts

- **Manager page.** Above 1100px, show two columns: bio and fantasy information on the left,
  roster and transactions on the right. Let the awards row wrap inside the left column.
  Files: `Manager.svelte`, `ManagerAwards.svelte` (both changed).
- **Matchups.** Widen the list on desktop, and allow two columns of matchup cards above
  1200px. This depends on the readability fixes in workstream C landing first.
- **Rosters.** Add a row of team-name chips at the top, each jumping to that team's anchor.
  Make it a new league component, mounted in the route file.
- **Awards.**
  - Fix podium labels overlapping the avatars (`Awards.svelte:159-175`).
  - Tighten the vertical spacing.
  - Consider collapsing past years behind a "Show earlier seasons" control. This page is
    7,200px tall.

**Checks.**
- Every page's heading looks the same at both widths.
- Layout shift measured before and after with the checking snippet.

---

## C. Readable on phones (effort M–L, highest merge risk)

**Covers:** text shrunk to 5–9px, the Standings table overflow, the order of the Drafts page,
and small tap targets.

**The rule.** Nothing smaller than **12px** anywhere; table data at least **14px**. When
something doesn't fit, change the layout: stack it, scroll it with a sticky first column, or
drop a column. Never shrink the text.

### C1. Records (changed)

- Delete the shrink rules in `RecordsAndRankings.svelte:454-531` and
  `Records/index.svelte:84-104`. They are `:global`, which is also why they leak onto
  Matchups.
- Replace the two SMUI button groups (seven buttons in total) with `SegmentedControl`.
  - First check it can handle seven options. It needs to scroll sideways or wrap cleanly. If it
    can't, add that to the primitive. It is ours, so this costs nothing in merges.
- Record tables: keep 14px text. On phones, let the table scroll sideways with a sticky name
  column.
- `PerSeasonRecords.svelte:136-143` (upstream) has a `:global` shrink rule. Override it in
  `_site.scss` rather than editing it.

### C2. Matchups (upstream, so make a minimal edit)

- In `Matchup.svelte:323,338-375`, the name and points rules are scoped. Delete the shrink
  media queries.
- Below 410px, switch the layout so each player's points drop under the player's name instead
  of sitting beside it in a shrinking cell. That is a small block of new CSS.
- Also raise the 0.5em team label (`:323`) to at least 12px.
- Expect this file to conflict on the next upstream merge, because of this change. Note it in
  `CLAUDE.md`'s list of files that differ from upstream on purpose.

### C3. Standings (changed)

- Remove the Div W, Div T, Div L and T columns from `columnOrder` (`Standings/index.svelte:22`)
  and from `sortOrder` (`:19`). This league has no divisions and no ties. Upstream's comment
  there invites exactly this edit.
- Make the Team column sticky on phones.
- Target width at 375px: about 430px, scrolling inside a container rather than the whole page.

### C4. Drafts (upstream, so reorder rather than rewrite)

- In season, the completed draft should lead. In `Drafts/index.svelte:25-36`, swap the two
  blocks when the league status isn't `pre_draft` or `drafting`.
- Put the projected next-year board behind a collapsed "Projected {year} draft order" control.
- The KEEPER tag (`DraftRow.svelte:94`, changed): raise it to at least 12px.
- The board's 70vh inner scroll (`Draft.svelte:112`, changed): on phones, let the page scroll
  instead.

### C5. Other small text and tap targets

- Manager page chips and captions: raise from 8.6–9.6px to 12px.
- Awards captions: raise from 7.2–9.6px to 12px.
- Transactions: raise position labels from 8.6px to 12px. Make the pagination arrows at least
  44px (`Pagination.svelte`, changed).
- Rivalry dropdowns: at least 44px tall.
- Resources podcast links: at least 44px tall.
- `SegmentedControl`: at least 44px tall (it is ours; 34px today).

**Checks.**
- The checking snippet must report a minimum font size of at least 12px on every page at 375px.
- No page may scroll sideways.
- Compare screenshots before and after for Matchups, Records, Standings and Drafts.

---

## D. Links between pages (effort S–M)

**Covers:** the missing cross-links, and clickable `div`s that should be real links.

- **Manager page → their rivalry page.**
  - Turn the Rival tile (`ManagerFantasyInfo.svelte:240`) into a "Head-to-head" link to
    `/rivalry?player_one=<id>&player_two=<id>`.
  - First check which ID the rivalry page expects.
- **Manager page → this week's matchup.**
  - A small "This week: vs {opponent}" line linking to `/matchups`.
  - It comes from the memoized `getLeagueMatchups()` and doesn't show in the offseason.
  - Put it in a new league component mounted in `Manager.svelte`.
- **Matchup cards and brackets → manager pages.**
  - In `Matchup.svelte` and `BracketsColumn.svelte` (upstream), wrap team names in
    `<a href="/manager?manager=N">`, using the existing index lookup.
  - Use a real link, not a `gotoManager` click handler, so it opens in a new tab and works from
    the keyboard.
- **Home page NFL week banner → `/matchups`.**
- **Clickable `div`s → real links:**
  - `Standing.svelte:32`
  - `Bar.svelte:130`
  - the home page champion panel
  - "( view more )" at `Transactions.svelte:77,93`

  Each becomes an `<a href>` with the same styling. Hall of Fame and Last Season already show
  the pattern.

**Checks.** On each page, Tab reaches every new link, and Cmd-click opens it in a new tab.

---

## E. Content and copy (effort M, mostly writing)

**Covers:** the bios, the home page text, Resources, the countdown, and lore.

### E1. Bio fixes (leagueInfo.js, ours)

- Typos at `:129`, `:165`, `:177`.
- `:177`: 32/59 is **54.2%**.
- Leave "Marvey Mudd" at `:201` (Malcolm's bio); it reads as a deliberate joke.
- **Waiting on Garrett:** the Tucker Harris "young boys" line and Kevin's stats.

### E2. One Mudd League line per active bio

- Pull a candidate fact per manager from `docs/league-lore.md`: career MVP, best keeper,
  longest streak, or perfect lineups.
- **Re-derive each number from the current data at the time of writing**, per the
  verify-stats rule. Then show Garrett the ten lines before they go in.

### E3. Home page

- Draft a shorter `homepageText`:
  - a two- or three-sentence introduction;
  - a **"Find your way"** row: this week's matchups · standings · Trophy Room · constitution;
  - a single link to the constitution in place of the rules detail, which already lives there;
  - and no hard-coded champion paragraph (`:47`), since the right-rail panel updates itself.
- This moves power rankings and the champion panel from y≈1800 to near the top on phones.
- **Garrett approves the copy.**

### E4. Resources

- Add a new `src/lib/Resources/LeagueLinks.svelte`, mounted first in the route file:
  - Keeper Draft Board, the Sleeper league, Constitution, The Mudd Report;
  - half-PPR rankings, an injury report, a FAAB guide.
- Upstream's `Resources.svelte` stays as is, below it.
- **News feed: move it to the bottom of the page** (decided). It currently returns five
  podcast episodes and nothing from Reddit.

### E5. In-season countdown

- On the home page right rail (`routes/+page.svelte`, changed), after the draft, reuse
  `Countdown` to count down to the trade deadline, then to the playoffs.
- **Check against Sleeper first:** exactly when "trade deadline week 12" locks, and where to get
  the kickoff date of week 13 or week 16.
  - `nflState` may carry the season's start date, which with the week number gives the date.
  - If no reliable date exists, show "Trade deadline: end of week 12" without a ticking clock.

### E6. Lore

- Most of this belongs on the Seasons pages; see the History plan.
- Optionally, add a hand-picked lore card on Trophy Room: five to eight facts in a small static
  file, never the 97 KB `narratives.json`.

---

## F. Rules, data and documentation (effort S)

These can go in alongside anything else.

- **Constitution: the 2026 roster change** (voted 7–3, confirmed):
  - five bench spots, thirteen roster spots, thirteen rounds (`:347`, `:418`);
  - the matching line in `homepageText` (`:45`);
  - the "14" mentions in `src/routes/CLAUDE.md:55`, `src/lib/utils/CLAUDE.md:83`, and
    `Draft.svelte:63`.
  - Consider a one-line note in the constitution recording when this changed.
- ~~Gaps in the constitution~~. **Dropped:** the league has no rules for draft order, the
  keeper deadline, tiebreakers and seeding, or inactive managers, and the site won't invent
  them.
- **Blog post types:**
  - `mudd-preview` skill: pass `--type Preview` to `publish-article.mjs`.
  - Garrett retags the three existing previews in Contentful.
- **`pull-league-history.py`:**
  - `weeks_played` should count only weeks in which points were scored;
  - ownership spans should stop at the last played week.

  This is the same fix as step 0 of the History plan, so do it there once.
- **`CLAUDE.md` corrections:**
  - unset manager fields are hidden, not shown as "?";
  - rivals are real pairings now (see the comment above `managers` in `leagueInfo.js`), and
    that comment's own "?" note is stale too;
  - the Conventions section says the blog is off;
  - BBrown16's team name is out of date;
  - `narratives.json` has 302 facts, not 278;
  - add the new override stylesheet and `Matchup.svelte` to the notes on files that differ from
    upstream.
- **End-of-season checklist.** Add to `CLAUDE.md`:
  - re-run `pull-league-history.py`, `derive-narratives` and `derive-site-data`;
  - update any remaining hand-written champion lines.

### Asks for other managers

Garrett can send this as one message; the answers go straight into `leagueInfo.js`.

> For the league site, reply with any of these you're happy to share:
> 1. Favourite NFL team
> 2. Best way to reach you about trades (Sleeper DM, text, …)
> 3. How willing are you to trade, 1–10
> 4. Your fantasy philosophy in one line
> 5. Favourite player, all-time or right now
> 6. The position you value most
> 7. The year you started playing fantasy
>
> And kshoyer, tuckersdumbteam, TnT44: please set a team name in Sleeper.

---

## Order of work across both plans

| # | Work | Effort | Notes |
| --- | --- | --- | --- |
| — | **Garrett's decisions** (see below) | — | Unblocks F and parts of E; ask now |
| 1 | **A. The nav** | M | Every page benefits; new pages need its groups |
| 2 | **C3 + C2 + C1.** Standings, Matchups, Records on phones | M | The worst phone problems, on the most-used pages |
| 3 | **History step 0 + 1.** Game table and schedule luck | M | Most useful mid-season |
| 4 | **B1–B3.** Page headers, text fixes, layout jump | M | History pages reuse `PageHeader` |
| 5 | **D. Links between pages** | S–M | |
| 6 | **History step 2.** Head-to-head grid | S | |
| 7 | **C4–C5, B4–B5.** Drafts, small text, blog, desktop layouts | M | |
| 8 | **E. Content**, as Garrett's answers arrive | M | |
| 9 | **History steps 3–4.** Seasons, Stat Lab | L | Offseason-friendly |

F runs alongside whenever a decision comes back.

## Decisions for Garrett

**Decided on 2026-10-02:**

1. **The 2026 roster change was voted on, 7–3.** Go ahead with the edits in F: five bench
   spots, thirteen roster spots, thirteen rounds. Note the change in the constitution.
2. **"Marvey Mudd"** is in Malcolm's bio (`:201`), not Kevin's or Tucker's. "A certain Marvey
   Mudd running back" reads as a deliberate joke, so leave it unless Garrett says otherwise.
3. **There are no rules yet for draft order, the keeper deadline, tiebreakers and seeding, or
   inactive managers.** Drop this from the constitution work. Don't invent rules. If the league
   ever wants them written down, the starting point would be how Sleeper's settings already
   behave, put to a vote.
4. **Drop the Home tab outright,** and follow the plan's other nav recommendations. The seal
   links home.
5. **Move the news feed** below the league links and upstream's list. Don't remove it.

**Still open:**

6. **The Tucker and Kevin bios.** The "young boys" line in Tucker's bio and Kevin's
   "420/69/666" stats: keep, soften or cut?
7. **Home page copy.** Approve the shorter `homepageText` before it goes live.

---

## Checking snippet

Paste into the browser's JavaScript tool on any page, after the data has loaded.

```js
(async () => {
  const vis = (el) => { const r = el.getBoundingClientRect(), s = getComputedStyle(el);
    return r.width && r.height && s.visibility !== 'hidden' && s.display !== 'none'; };
  // smallest rendered text
  const sizes = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) { const n = walker.currentNode, p = n.parentElement;
    if (n.textContent.trim() && p && vis(p)) sizes.push([parseFloat(getComputedStyle(p).fontSize), n.textContent.trim().slice(0, 30)]); }
  sizes.sort((a, b) => a[0] - b[0]);
  // small tap targets
  const small = [...document.querySelectorAll('a, button, [role=button], select, input')]
    .filter(vis).map((el) => [el.getBoundingClientRect(), el])
    .filter(([r]) => r.height < 44 || r.width < 44)
    .slice(0, 10).map(([r, el]) => `${Math.round(r.width)}x${Math.round(r.height)} ${el.textContent.trim().slice(0, 20)}`);
  // layout shift so far: only exposed through a buffered observer, not getEntriesByType
  const cls = await new Promise((resolve) => {
    let total = 0;
    const obs = new PerformanceObserver((list) => {
      for (const e of list.getEntries()) if (!e.hadRecentInput) total += e.value; });
    obs.observe({ type: 'layout-shift', buffered: true });
    setTimeout(() => { obs.disconnect(); resolve(total); }, 100);
  });
  return { width: innerWidth, horizontalScroll: document.documentElement.scrollWidth > innerWidth,
    minFont: sizes.slice(0, 5), smallTargets: small, cls: Math.round(cls * 100) / 100 };
})();
```

The layout-shift total covers everything since the page loaded. Reload and wait for the data
before running it, or the number will be low.
