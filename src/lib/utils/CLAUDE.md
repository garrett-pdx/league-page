# CLAUDE.md — config & data layer

This directory is where the league is *configured* and where every byte of Sleeper data
enters the app. See the root `CLAUDE.md` for the league's facts (IDs, managers, rules).

## leagueInfo.js — the config file

The one file the upstream template exists to have you edit, and the first stop for almost
any league-customization request:

- `leagueID` — the **current season's** Sleeper league ID only. Everything else walks
  backwards through `previous_league_id` on its own; do not list old seasons here.
- `leagueName`.
- **`dues` is gone.** Upstream exports it here and the constitution page renders the
  amount and the payout math from it; this league doesn't track dues on the site, so the
  export, its re-export in `helper.js`, and the constitution's Section 7 were all removed
  together. If a future upstream merge reintroduces a `dues` import, delete it rather than
  restoring the constant.
- `dynasty` — **`false`** for this league. It's a keeper league, and the template defaults
  to `true`. See "There is no keeper league type" below for what this flag does and,
  more importantly, what it doesn't.
- `enableBlog` — currently `false`; turning it on requires the Contentful env vars
  (`VITE_CONTENTFUL_ACCESS_TOKEN`, `VITE_CONTENTFUL_SPACE`,
  `VITE_CONTENTFUL_CLIENT_ACCESS_TOKEN`).
- `homepageText` — a raw HTML string, injected into the home page with `{@html}`. This is
  the intended way to customize the home page's copy. Hand-written trusted content only.
- `managers` — one object per manager, keyed by **`managerID`** (the Sleeper `user_id`).
  The commented-out block at the bottom of the file is upstream's canonical, up-to-date
  manager shape; it is deliberately left commented so upstream can revise it without
  merge conflicts. **Copy from that block, don't copy from the three older examples
  above it**, and leave it in place. Ignore the deprecated `roster` and `tookOver` fields.
  Photos referenced here live in `static/managers/`.

An empty `managers` array is valid — the manager pages just stay generic, and the home
page skips the click-through to a manager bio.

**Two fields are required despite the docs implying everything optional can be nulled**,
because they're rendered unguarded:

- `photo` — both `ManagerRow.svelte` (`img.photo`) and `Manager.svelte` (`img.managerPhoto`)
  bind `src` with no `{#if}`, so a missing photo is a broken image. Every manager here
  points at a local file in `static/managers/`.
- `rival` — `ManagerFantasyInfo.svelte` reads `rival.link`, `rival.image` and `rival.name`
  unguarded (search `infoRival`), so omitting it **throws on the manager detail page**.
  `link` is an index into the `managers` array — it shifts if you reorder entries — and
  `null` links back to the all-managers page.

Every other field is properly `{#if}`-guarded and safe to omit.

`managerID` must be a user Sleeper knows about somewhere in the league history —
`ManagerRow.svelte` does an unguarded `leagueTeamManagers.users[manager.managerID]` lookup
for the commissioner badge. This is why a departed manager can safely be listed (Jordan
Leonard is), but an invented ID cannot.

## There is no keeper league type

`dynasty` is a two-state, **purely cosmetic** flag. It is read in exactly three places,
none of which touch draft or roster mechanics:

- `src/lib/Resources.svelte` — filters the resource links (`dynastyOnly` / `redraftOnly`).
- `src/lib/Managers/ManagerRow.svelte` — shows the "Rebuild" mode badge only when true.
- `helperFunctions/news.js` + `routes/api/fetch_serverside_news` — picks which RSS feeds
  to pull.

The string "keeper" appears **nowhere** in `src/` outside these CLAUDE files. There is no
keeper cost, no keeper count, no inflation, and no third league type. `false` here means
"not dynasty" and is the right setting, but it buys nothing keeper-specific — it just
swaps dynasty content for redraft content.

**Sleeper does supply the data; the template ignores it.** `/draft/{id}/picks` returns
`is_keeper` (`true` or `null`) on every pick, and because a keeper consumes the pick slot
it costs, the round of that pick *is* the keeper cost. Verified live on the league's 2025
draft: 14 rounds, 140 picks, 18 flagged `is_keeper`, spread across all 10 teams — e.g.
TnT44 kept Josh Jacobs at R2 and Justin Jefferson at R3; Gurret kept Trey McBride at R13.

**We now surface that.** `completedNonAuction` in `helperFunctions/leagueDrafts.js` sets
`keeper` on the draft cell and `Drafts/DraftRow.svelte` renders a corner badge, so a past
draft shows which picks were spent on keepers and — because the badge sits in the round it
cost — what each one cost. 75 badges render across 2022-2025, matching `keepers.json`
exactly; the page reads live Sleeper while that file was pulled independently, so the two
agreeing is a genuine cross-check. Pre-draft boards show no badges, which is correct.

Anything richer than "this pick was a keeper" — cost inflation, next-year projections,
who can keep whom — belongs in the keeper draft board project, not here.

## Manager bios: where the numbers come from

Every manager is a former Claremont-Mudd-Scripps football player, and their bios are built
from their `cmsathletics.org` roster page. Two things to know before editing one.

**The site contradicts itself.** Each player page has prose bio copy AND structured
Statistics tables, and they frequently disagree. Malcolm Stolarski's prose says he started
every game as a true freshman and started all of 2016-17; his Participation table says
2015: 0 starts, 2016: 2, 2017: 1. Kevin Shoyer's prose claims seven tackles for loss in
2017; his career table totals 1.

**League policy, set by Garrett: when the two conflict, use whichever sounds better.**
This is a league page, not a record book. The constraint is that the number must actually
appear somewhere on the school's own page &mdash; pick between two published figures, never
invent a third. Both current conflicts are resolved toward the prose.

**Two facts confirmed by Garrett that the source can't back up.** `Kabroa` is Kanoa
Gilliland &mdash; the handle doesn't contain the name, so this mapping came from Garrett, not
from the page. And Jonah Cartwright attended **Harvey Mudd**; the CMS site has it wrong, so
his bio's "fellow Harvey Mudd running back" line is correct as written. Don't rewrite
either one against the website.

**Scraping these pages needs the browser, not WebFetch.** The Statistics tab
(`#ui-id-3`) populates client-side, so WebFetch sees "no statistics available" and reports
the player has none. Use the Browser tools: navigate, click `ui-id-3`, then read the tables
under the "Career Statistics" heading. The `Historical` tab holds year-by-year
height/weight and jersey changes. Offensive linemen genuinely have empty career tables.

## helper.js is a barrel, not logic

`helper.js` re-exports `leagueInfo.js` plus everything in `helperFunctions/`. Routes and
components import from `$lib/utils/helper`; keep it that way. When you add a helper, add
its export here too rather than letting callers deep-import.

## helperFunctions/ — the Sleeper data layer

One file per domain concept (`leagueRosters`, `leagueMatchups`, `leagueRecords`,
`leagueTransactions`, `leagueAwards`, `leagueDrafts`, `leagueStandings`, `leagueBrackets`,
`rivalryMatchups`, `nflState`, `players`, `news`). `universalFunctions.js` holds the
shared formatting/lookup utilities (`getTeamFromTeamManagers`, `gotoManager`, `cleanName`,
`round`, `getAvatar`, …).

Three patterns run through all of them, and new code should follow them:

**1. Store-as-cache, checked first.** Every loader starts by returning the memoized value
out of `$lib/stores` if it's already populated, and only fetches otherwise:

```js
if(get(leagueData)[queryLeagueID]) return get(leagueData)[queryLeagueID];
```

The stores in `src/lib/stores.js` are a per-session cache, not app state anyone mutates
from the UI. A page navigation must not re-hit Sleeper for data already loaded.
`players.js` adds a second tier on top of this — `localStorage` with an expiration, and a
`stale` flag so the UI can render immediately and refresh behind itself.

**2. Walk the league history by `previous_league_id`.** Anything "all-time" (records,
awards, team/manager mapping) loops from `leagueID` backwards until the ID is falsy or
`0`, building a `[year][roster_id]` map — see `leagueTeamManagers.js`, the pattern the
others follow. For this league that's five seasons, 2022–2026. Roster IDs are only
meaningful *within* a season, which is why the map is keyed by year first; never assume a
roster ID identifies the same manager across seasons.

**3. Fan out with `waitForAll`, don't await in sequence.** `waitForAll` is just
`Promise.all` with a nicer name. Sleeper calls are independent and slow; issuing them
serially is the main way this site gets sluggish.

## The Reddit half of the news feed is permanently dead (handled)

`news.js` fetches Reddit's `new.json` from the browser and **Reddit sends no
`Access-Control-Allow-Origin`**, so it is CORS-blocked every time. Server-side is no better
— Reddit answers that with an HTML block page, not JSON. This is not fixable from here;
treat the Reddit source as gone.

What *was* fixable, and is fixed: the failure used to take the whole page down. `getFeed`'s
`.catch(err => console.error(err))` left `res` undefined, the next line threw on `res.ok`,
the whole `waitForAll` rejected, `getNews` destructured `undefined`, and /resources rendered
"Something went wrong: (intermediate value) is not iterable" instead of any articles.
`getFeed` now returns `[]` on a rejected fetch and `getNews` no longer destructures blind,
so the page degrades to the `/api/fetch_serverside_news` sources (podcasts, FTN) and simply
omits Reddit.

**Expect a CORS error in the console on /resources.** It is the known one, it is not a
regression, and the visible page is correct. Unrelated to `dynasty`, which only picks
r/DynastyFF vs r/fantasyfootball — both on reddit.com.

## Sleeper API notes

Public, read-only, unauthenticated, base `https://api.sleeper.app/v1`. There is no write
path and there shouldn't be one. Endpoints in use: `/league/{id}`, `/league/{id}/users`,
`/league/{id}/rosters`, `/league/{id}/matchups/{week}`, `/league/{id}/transactions/{week}`,
`/league/{id}/winners_bracket` + `/losers_bracket`, `/league/{id}/drafts`,
`/draft/{id}/picks`, `/players/nfl`, `/state/nfl`, plus the unversioned
`/projections/nfl/{year}/{week}`.

`/players/nfl` is **~5MB** — that's why it's fetched through the server route
`/api/fetch_players_info` and cached in `localStorage`, not requested from every page.
Don't add a direct browser call to it.
