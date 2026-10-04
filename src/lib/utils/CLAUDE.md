# CLAUDE.md — config & data layer

This directory is where the league's configuration enters the app and where every byte of
Sleeper data does. The league's own facts are in `league/NOTES.md`.

## leagueInfo.js — the config loader

Nothing league-specific is written here. It reads `league/league.json` (through the `$league`
alias, which `LEAGUE_DIR` can repoint to preview another league) and the optional `home.md` and
`constitution.md`, and exports what the components import:

- `leagueID` (`sleeperLeagueId`, the **current season's** ID; history walks
  `previous_league_id`), `leagueName`, `leagueShortName`, `leagueDescription`, `siteUrl`,
  `founded`, `dynasty`, and `league` (the whole config).
- Blog: `blogBackend` ("markdown" by default, "contentful", "none"), `enableBlog`, `blogTitle`,
  `blogIntro`, `contentfulTypes`, `enableComments` (Contentful only, and only with a server-side
  management token; see the comment in the file).
- `homepageText` (home.md rendered) and `constitution` (constitution.md parsed into numbered
  sections by `parseConstitution()` in `markdown.js`, or null).
- `leagueLinks`, `elsewhereLinks`, `navLinks` (links with `nav` set, for the League menu);
  `{sleeper}` in a URL is the league's Sleeper page, and links to a disabled feature are dropped.
- `preSleeperSeasons` / `preSleeperSeason(year)`, `pageIntro(key)`, `photoUrl(photo)`.
- `managers`, **in the shape the components were written against**: `managerID`, a resolved
  `photo` URL and `rival: { name, link, image }`, where `link` is an index into this array (or
  null). league.json names a rival by `userId` instead, so reordering managers can never quietly
  re-pair them; the index is computed here. A rival can also be a named non-manager
  (`everyone.png` and `question.jpg` are built-in photos).

Photos are bundled with `import.meta.glob` from `league/managers/`, so they are fingerprinted.
Optional files are globs rather than imports, so a league without one still builds.

An empty `managers` array is valid (the Managers tab hides); `scripts/sync-managers.py` fills it
from the dataset. `managerID` must be a user Sleeper knows somewhere in the league's history:
`ManagerRow.svelte` looks the user up unguarded for the commissioner badge.

## There is no keeper league type

`dynasty` (league.json) is a two-state, **purely cosmetic** flag. It is read in exactly two places, neither
of which touches draft or roster mechanics:

- `src/lib/Resources.svelte` — filters the resource links (`dynastyOnly` / `redraftOnly`).
- `helperFunctions/news.js` + `routes/api/fetch_serverside_news` — picks which RSS feeds
  to pull.

There is no keeper league type in the site itself. Every keeper feature is read-only: the draft
badge below, and the Seasons pages' keeper list, which reads the pulled `keepers.json` (each
keeper's cost and lineage, and, when league.json has a `keepers.rule`, whether the cost matched
it — computed offline by the pull).

**Sleeper supplies the data.** `/draft/{id}/picks` returns `is_keeper` (`true` or `null`) on
every pick, and because a keeper consumes the pick slot it costs, the round of that pick *is*
the keeper cost. `completedNonAuction` in `helperFunctions/leagueDrafts.js` sets `keeper` on the
draft cell and `Drafts/DraftRow.svelte` renders a corner badge, so a past draft shows which picks
were spent on keepers and what each cost. The page reads live Sleeper while `keepers.json` is
pulled independently, so the two agreeing is a genuine cross-check. Pre-draft boards show no
badges, which is correct.

## helper.js is a barrel, not logic

`helper.js` re-exports `leagueInfo.js` plus everything in `helperFunctions/`. Routes and
components import from `$lib/utils/helper`; keep it that way. When you add a helper, add
its export here too rather than letting callers deep-import.

## helperFunctions/ — the Sleeper data layer

One file per domain concept (`leagueRosters`, `leagueMatchups`, `leagueRecords`,
`leagueTransactions`, `leagueAwards`, `leagueDrafts`, `leagueStandings`, `leagueBrackets`,
`rivalryMatchups`, `nflState`, `players`, `news`), plus three of ours that read committed
files from `static/data/` instead of Sleeper (see "Static-data readers" below). `universalFunctions.js` holds the
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
others follow. Roster IDs are only
meaningful *within* a season, which is why the map is keyed by year first; never assume a
roster ID identifies the same manager across seasons.

**3. Fan out with `waitForAll`, don't await in sequence.** `waitForAll` is just
`Promise.all` with a nicer name. Sleeper calls are independent and slow; issuing them
serially is the main way this site gets sluggish.

## Static-data readers (ours)

Three helpers fetch our own committed files rather than Sleeper. They follow a different cache
pattern from the Sleeper loaders: a module-level promise per file, **never memoizing a
rejection**, and they take SvelteKit's `fetch` (`getLeagueGames(fetch)`) so a `load()` can call
them during SSR. No stores, no `localStorage`.

- **`leagueHistory.js`** → `league-history.json`: `getLeagueHistory`, `getManagerCareer`, and
  the full 1–10 finishes Sleeper can't give.
- **`leagueGames.js`** → `games.json`: `getLeagueGames` decodes the columnar file into one row
  per team per game, and the pure functions every history page computes with — `filterGames`,
  `allPlay`, `headToHead`, `standingsFrom`, `liveSeasonGames` (the same row shape built from live
  Sleeper matchups, so Standings' luck never lags), `benchPoints`, `lineupEfficiency`,
  `lineupTotals`. Rows are keyed on `user_id`. An override game's `max_pf` is null; skip
  nulls rather than treating them as zero. `median` (median-game result) and `leg` (two-week
  playoff rounds) are null unless the league has them; `standingsFrom` counts median results.
- **`seasonNotes.js`** → `season-notes.json`, `keepers.json`, `players.json`, for the Seasons
  archive only.

The sizes and the rule against fetching anything bigger are in the root `CLAUDE.md`.

## Small utils of ours

- **`tabs.js`** also exports `findTab`, `currentDest` and `tabAliases`, the one lookup behind
  the nav highlight and the tab title.
- **`pageTitle.js`** — `pageTitle(page)`: an error page is "Not found", then a `title` from
  `load()`, then the nav label, then upstream's capitalised path. `titleFromSlug` for blog posts.
- **`managerLink.js`** — `managerHref` / `managerIndex`: a real `/manager?manager=N` address
  for a team, following `gotoManager()` step for step. Use it wherever upstream used a click
  handler on a div; a link opens in a new tab and is reachable by keyboard.

## Transactions degrade, they don't throw

`getLeagueTransactions` used to destructure the result of a `.catch(console.error)` and threw
"Cannot destructure 'transactionsData'" whenever a Sleeper fetch failed, which crashed /manager.
It now returns no transactions (and doesn't cache them) when the comb fails, and tolerates a
failed `getNflState`.

`getLeagueTeamManagers` also returns `neverRostered`: accounts in a season's user list that
never owned or co-owned a roster (a commissioner's second account, an invite never accepted).
Pages that list every manager leave them out.

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

`/players/nfl` is **~15MB** (was ~5MB in 2025) — that's why it's fetched through the server route
`/api/fetch_players_info` and cached in `localStorage`, not requested from every page.
Don't add a direct browser call to it.
