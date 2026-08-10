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

Hand-written HTML — league rules, scoring, keeper rules — with a manually maintained
table of contents wired up by the `goToSection` refs at the top of the file. This is pure
content and the one place in `routes/` you should edit freely. **If you add or remove a
section, update the table of contents to match** (nothing does it automatically). Keeper
rules restated here must agree with the keeper draft board's `CLAUDE.md`, which is the
source of truth for that wording.

**It is still upstream's demo-league text.** The `<h1>` reads "LEGENDS LEAGUE
CONSTITUTION" (hardcoded, not `leagueName`), and Sections 1–6 describe a 12-team dynasty
league — wrong roster shape, wrong scoring, rookie drafts this league doesn't hold, no
keeper rules at all. Treat every word as a placeholder to be rewritten, not as a starting
draft to tweak. Section 7 (League Finances) has already been removed along with `dues`.

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
