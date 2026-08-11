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

## `+layout.svelte`

`<Nav />`, `<slot />`, `<Footer />`, plus `injectAnalytics` from `@vercel/analytics`. The
nav's structure comes from `src/lib/utils/tabs.js`, not from this file — add or reorder
nav entries there. `tabs.js` already links out to Sleeper using `leagueID`; a link to the
keeper draft board belongs in the same place (or under `/resources`).

## `+page.svelte` at the root — the home page

The league home page. Left column: league name, `homepageText`, `<PowerRankings />`.
Right rail: NFL season/week banner, the reigning champion from `getAwards()` (click-through
to the manager page when `managers` is populated), and recent `<Transactions />`.

Customize it through `homepageText` in `src/lib/utils/leagueInfo.js` before reaching for
the component itself.

## `constitution/`

This league's actual rules, rewritten from scratch — nine sections covering format,
rosters, scoring, keepers, the draft, waivers, trades, the postseason and league votes.
Every mechanical rule was sourced from the live Sleeper config rather than assumed, so
treat the numbers as load-bearing: no kicker or defense slot, half-PPR, 14-round snake,
$100 FAAB, week 12 trade deadline, four-team playoff over weeks 16-17.

Pure content, and the one place in `routes/` to edit freely. Two things to preserve:

- **The table of contents is manual.** It's a `<nav>` of `<button>`s bound to `goToSection`
  refs declared at the top of the file. Add or remove a section and you must update both
  the refs and the nav. It was originally a stack of clickable `<h3>`/`<h4>`s, which made
  every section title appear twice in the document outline and left the whole TOC
  unreachable by keyboard — don't regress it back to headings.
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

- `fetch_players_info` — proxies and post-processes Sleeper's ~5MB `/players/nfl` plus
  weekly projections. This exists so browsers don't pull that payload directly; keep it
  that way.
- `fetch_serverside_news` — RSS/news aggregation (`fast-xml-parser`).
- `getBlogPosts` / `getBlogComments` / `addBlogComments/[id]` — Contentful. Inert while
  `enableBlog` is `false`.
- `checkVersion` / `checkGlobalVersion` — upstream's fork-update check; it compares
  `src/lib/version.js` against `league-page.nmelhado.com`. Leave both alone. `checkVersion`
  reporting an update is the cue to merge upstream, not a bug.

Anything needing a secret (Contentful tokens) must stay in `api/` — env vars are read
server-side there and must never be shipped to the client.
