# CLAUDE.md — routes

SvelteKit file-based routing. See the root `CLAUDE.md` for the fork constraint that
governs how freely each of these files can be edited.

## Page shape

Every page directory is a pair:

- **`+page.js`** — a `load()` that calls helpers from `$lib/utils/helper` and returns
  **unawaited promises**, usually bundled with `waitForAll`.
- **`+page.svelte`** — resolves those promises in `{#await}` blocks, rendering an
  `@smui/linear-progress` bar while pending and a message on `{:catch}`.

```js
// +page.js
export async function load({fetch}) {
    const rostersInfo = waitForAll(getLeagueData(), getLeagueRosters(), loadPlayers(fetch));
    return { rostersInfo };   // NOT awaited
}
```

Returning the promise is deliberate: the nav, footer, and page shell paint immediately
while Sleeper is still answering. `await`ing inside `load()` blocks the whole route on the
slowest call — don't "clean it up" into an await.

`load()` takes SvelteKit's `fetch` and passes it to `loadPlayers(fetch)` so the call works
during SSR. Keep threading it.

Pages are thin: they render a feature component out of `$lib/components` (`<Standings />`,
`<Records />`, `<MatchupsAndBrackets />`, …). Logic belongs in the component or the helper,
not in the route file.

**Every page's heading is a `PageHeader` (`$lib/Design`) mounted here, in the route file**,
above the `{#await}`: it paints before the data, and the upstream component underneath only
lost its old heading. That is why most upstream route files differ from upstream by a few
lines. Three routes also return a `title` from `load()` for the browser tab: `manager` (the
manager's name, a synchronous array lookup), `seasons/[year]` ("2024 Season") and
`blog/[slug]` (words from the slug, because the real title is an async Contentful call). See `src/lib/utils/pageTitle.js`.

## `+layout.svelte`

`<Nav />`, `<slot />`, `<Footer />`, plus `injectAnalytics` from `@vercel/analytics`. The
nav's structure comes from `src/lib/utils/tabs.js`, not from this file — add or reorder
nav entries there. `tabs.js` already links out to Sleeper using `leagueID`; a link to the
keeper draft board belongs in the same place (or under `/resources`). Both now exist: the
board is under League → Rules & Tools, and `/resources` leads with `LeagueLinks`.

## `+error.svelte`

Upstream's "Hut, Hut, Blue 404!" page, unchanged. Its tab title is "Not found" (or "Error"
for anything but a 404) from `pageTitle.js`; before that it borrowed the first path segment, so
`/seasons/1999` was titled "Seasons".

## `+page.svelte` at the root — the home page

The league home page. Left column: league name, `homepageText`, the featured blog post,
`<PowerRankings />`. Right rail: the NFL season/week banner (a link to /matchups), the draft
countdown or, once the draft is done, `SeasonMilestone` from `$lib/Home` (trade deadline, then
playoffs, as "N weeks away" with no ticking clock), the reigning champion from `getAwards()`
(one `<a class="champLink">` to the manager page when `managers` is populated), and recent
`<Transactions />`.

**Below 950px the two columns become one, in reading order:** every block is a flex item of
`#home` with a CSS `order` — intro, week banner, milestone, power rankings, champion, blog
post, transactions. The blog post is its own `.text` block for exactly this reason. A new
block needs its own `order` or it lands at the end on phones.

Customize it through `homepageText` in `src/lib/utils/leagueInfo.js` before reaching for
the component itself. The hand-written champion paragraph that used to sit in `homepageText`
is gone on purpose: the right-rail panel updates itself, and the paragraph went stale every
season. The current copy is awaiting Garrett's approval.

## `seasons/` (ours)

`/seasons` is a card per season; `/seasons/[year]` is one page per year, 2021 to the current
season, rendered by `$lib/Seasons/SeasonPage`. `[year]/+page.js` is the one load in the app
that **awaits** something: it awaits `league-history.json` (memoized, small) only to decide
whether the year exists, and throws SvelteKit's `error(404)` for one that doesn't, so a bad
year is a real 404 rather than an empty page. Everything else it returns unawaited, as usual.
2021 is the ESPN season: a short page with the carried-over draft and no standings, because
none exist. The season in progress is labelled as such and has no final table.

## `stat-lab/` (ours)

Filter, sort and chart over `games.json` and `league-history.json` (`$lib/StatLab`). The
whole view lives in the query string, so a chart can be linked from a post; Back undoes a
preset or a narrowing. First release: Games, Seasons and Careers datasets, 13 measures, bar /
line / scatter charts with a sortable table under each, six presets, no chart library.

## `constitution/`

This league's actual rules, rewritten from scratch — nine sections covering format,
rosters, scoring, keepers, the draft, waivers, trades, the postseason and league votes.
Every mechanical rule was sourced from the live Sleeper config rather than assumed, so
treat the numbers as load-bearing: no kicker or defense slot, half-PPR, 13-round snake
(14 through 2025; the five-spot bench and the lost round were voted 7–3 for 2026), $100
FAAB, week 12 trade deadline, four-team playoff over weeks 16-17.

Pure content, and the one place in `routes/` to edit freely. Three things to preserve:

- **Each section is a `<details>`, collapsed by default**, with the `<h2>` inside the
  `<summary>`. `bind:this` for a section points at the `<details>`, not the heading.
  `goToSection` walks up from its target opening every `<details>` ancestor before it
  measures — a collapsed section lays out none of its children, so a subsection ref inside
  one measures at the wrong position. It then waits a frame, because the expanded height
  is not real until the next one. Sections are left uncontrolled (no `open={...}`) so a
  reader's own toggling is never fought by a reactive value; **Expand all / Collapse all**
  set `.open` imperatively. That control is not decoration: find-in-page does not reliably
  match text inside a closed `<details>`, and this is a document people search for one rule.
- **The table of contents is manual.** It's a `<nav>` of `<button>`s bound to `goToSection`
  refs declared at the top of the file. Add or remove a section and you must update both
  the refs and the nav. It was originally a stack of clickable `<h3>`/`<h4>`s, which made
  every section title appear twice in the document outline and left the whole TOC
  unreachable by keyboard — don't regress it back to headings. It is kept alongside the
  accordion because `<summary>` only indexes the nine sections; the TOC is the only way to
  jump straight to a numbered subsection.
- **Body copy uses `var(--g555)`, not a hardcoded grey.** Upstream's `#777` measured
  ~3.6-4.2:1 against this page's gradient and failed AA in both themes.

Two rules here were decided by the league and are **the source of truth**, overriding the
keeper draft board where they disagree: same-round keeper collisions are resolved by the
manager's choice (section 4.5), and draft picks trade one for one (7.3). The board resolves
collisions by player rank instead; that divergence is accepted — see the root `CLAUDE.md`.

`dues` and its League Finances section were removed deliberately; this league doesn't
track dues on the site.

## `api/`

Server-side endpoints, running on Vercel functions:

- `fetch_players_info` — proxies and post-processes Sleeper's `/players/nfl` (~15MB as of
  2026-10; it was ~5MB when this note was first written) plus weekly projections. This
  exists so browsers don't pull that payload directly; keep it that way.
- `fetch_free_agents` — ours, backs `/free-agents` (search free agents by depth-chart slot,
  "every RB2"). Every QB/RB/WR/TE with a depth rank, injury, season snap share and Sleeper
  trending adds; rostered players carry `own` (owner user_id → Sleeper handle via `owners`) and
  show only when the page's "Show rostered" toggle is on. Despite the name it is no longer
  free-agents-only. Every outbound request is time-limited (Sleeper 20s, ESPN 8s, the whole ESPN
  step 15s): before that, one stalled request hung the whole response with no answer. CDN-cached 15 min; that header is what keeps the 15MB pull off every
  view. Traps it encodes:
  - `depth_chart_order` is per team+position (WRs share one sequence across LWR/RWR/SWR) and
    has gaps and duplicates, so it **dense-ranks** by sort rather than trusting the number.
  - **Players out for the season are excluded** — rostered ones too — and are removed
    *before* ranking so the next man up takes the slot. Sleeper can't tell you this (IR = four games, no return date),
    so the return date comes from ESPN's core API (`details.returnDate`; season-ending gets a
    date past the season, e.g. `2027-02-15`) compared against the end of the league's title
    week. Sleeper's `espn_id` is mostly null for fringe players, so it falls back to a
    name+team match against ESPN team rosters (Sleeper `WAS` = ESPN `WSH`).
  - ESPN failure **fails open**: everyone stays, with Sleeper's injury badge.
  - Projections are joined client-side from `fetch_players_info`, whose `round()` returns a
    **string** — `parseFloat` it before doing arithmetic.
- `fetch_serverside_news` — RSS/news aggregation (`fast-xml-parser`).
- `getBlogPosts` / `getBlogComments` / `addBlogComments/[id]` — Contentful. `getBlogPosts`
  is live (`enableBlog` is `true`); the two comment routes are inert because
  `enableComments` is `false` and no management token is deployed.
- `checkVersion` / `checkGlobalVersion` — upstream's fork-update check; it compares
  `src/lib/version.js` against `league-page.nmelhado.com`. Leave both alone. `checkVersion`
  reporting an update is the cue to merge upstream, not a bug.

Anything needing a secret (Contentful tokens) must stay in `api/` — env vars are read
server-side there and must never be shipped to the client.
