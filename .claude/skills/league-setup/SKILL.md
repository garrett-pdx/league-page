---
name: league-setup
description: Build a complete league website for a Sleeper fantasy football league from its league ID — configuration, the full history dataset, records and lore, colours and logo, manager pages, a constitution, the blog — and get it deployed. Use this when someone wants a site for their league, says "set this up for my league", gives a Sleeper league ID or sleeper.com/leagues link, is starting from a fresh copy of this template, or wants to re-point an existing site at a different league. Walks the whole job: checks the league works with the engine, interviews the commissioner once, writes league/, runs the data pipeline, drafts the content from real data, generates the brand, previews every page, and deploys.
---

# Setting up a league site

The result is a site that looks finished on day one: live standings and matchups, every past
season with its bracket and final table, records, Stat Lab, a Trophy Room, manager pages, a
constitution and a blog — in the league's own colours, with copy drawn from its real history.

Everything about the league goes in `league/` (see `league/README.md`; every config field is
documented in `schema/league.schema.json`). Nothing outside `league/` is edited for a league. If
the league needs something the engine can't express, that is an engine change: say so and stop
rather than special-casing the league inside a component.

## 0. Before starting

- Node 20 or 22 (`node --version`; a local `npm run build` refuses newer, though
  `DOCKER_BUILD=true npx vite build` works anywhere), Python 3.7+, git. `npm install` once.
- This is the template's repository, or a copy of it. If `league/league.json` still describes
  the demo league, everything in `league/` is about to be replaced; keep `league/README.md`.

## 1. Find the league and prove the engine handles it

The commissioner gives a Sleeper league ID: the number in `sleeper.com/leagues/<id>`, or from the
app's league settings. Then:

```bash
curl -s https://api.sleeper.app/v1/league/<id> | python3 -m json.tool | head -20   # name, season, status
scripts/try-league.sh <id>                # the whole data pipeline, in try-league/<id>/
LEAGUE_CONFIG=try-league/<id>/league.json python3 scripts/find-current-league.py   # a newer season?
python3 scripts/league-summary.py <id>    # the format, in plain terms
```

The site needs the **current** season's ID (Sleeper issues a new one each season). An old ID
works, but the site would show that season as current.

`try-league.sh` must finish with three `ok`s. A **FAIL** is a fault the engine does not handle;
report it to the commissioner with the message rather than working around it. **Warnings** in
`try-league/<id>/derive-site-data.log` are disagreements with Sleeper's own settled figures
(usually stat corrections after settlement, or a player whose position has changed); each one
prints the `league.json` override that would pin it. They are normal in old seasons and don't
block anything.

Read what you now know before asking anything: the summary, `try-league/<id>/docs/league-lore.md`
(~300 facts), the managers and seasons in `try-league/<id>/data/league-history.json`. A preview
of the site with no config at all: `npm run dev:league -- try-league/<id>` (port 5174).

## 2. Interview the commissioner, once

One message, grouped, with your proposed default for each answer so "yes" is a valid reply:

1. **Name.** The display name (may differ from Sleeper's) and a short name for tight spaces.
2. **History before Sleeper.** Founding year; seasons played elsewhere (platform, champions if
   known). If the first Sleeper season has two drafts, one is probably an imported draft from the
   old platform: confirm and record it as `history.preSleeper[].importedDraftId`.
3. **Look.** Two colours: a dark brand colour, and a championship colour (default gold). A
   tagline for the seal (default Fantasy, Keeper or Dynasty Football).
4. **Blog.** On (markdown, posts live in the repo; the default) or off. If on: its name, and the
   voice — who's "writing" it, how managers are named, running jokes, what's off limits.
5. **Managers.** Real names (optional; handles otherwise), hometowns, photos (Sleeper avatars
   are downloaded by default), and anything they want in their bio. **Personal details come
   from the commissioner or the managers themselves. Do not research private people online.**
6. **Rules.** An existing constitution or rules doc to work from, or draft one from Sleeper's
   settings. House rules Sleeper doesn't enforce: keeper costs, votes, deadlines.
7. **Links and domain.** League tools worth linking (a draft board, a group chat page), and the
   site's address if they have one.

## 3. Write `league/`

- **`league.json`**: start from the demo's shape; set `sleeperLeagueId`, `name`, `shortName`,
  `founded`, `description`, `siteUrl`, `theme` (`primary`, `trophy`, `tagline`), `blog`
  (`backend`, `title`, `intro`), `links`, `history.preSleeper`, and `dynasty` (true when
  `league-summary.py` says dynasty). `keepers.rule` only if the league confirms a round-based
  keeper cost; otherwise leave it out and the site reports keeper costs without claiming a rule.
  Validate against the schema (any JSON Schema validator, or your editor via `$schema`).
- **The data, for real:**
  ```bash
  python3 scripts/pull-league-history.py && npm run derive-site-data && npm run derive-narratives
  python3 scripts/sync-managers.py --photos    # every manager, with their Sleeper avatar
  python3 scripts/suggest-rivals.py            # review, then --write to fill rivals
  ```
  Then fill in the managers' real names and details from the interview.
- **`home.md`**: a short introduction (three sentences plus a line of links is plenty), from
  facts: founding, format, champions. Markdown; raw HTML allowed.
- **`constitution.md`**: `##` per section, `###` per rule; numbering is automatic. Sleeper's
  settings (`league-summary.py`) supply the roster, scoring, playoffs, waivers and trade deadline
  exactly; house rules come only from the commissioner. Never invent a rule — leave a section out
  rather than guess.
- **Bios** (`managers[].bio`, HTML): one or two lines of the manager's fantasy record from the
  lore and the data, plus whatever personal detail the commissioner supplied. Every number
  re-derived from `static/data/`.
- **`archive-facts.json`**: six to eight Trophy Room facts from `docs/league-lore.md`, in the
  shape documented in `src/lib/History/ArchiveCard.svelte`: completed seasons only, superlatives
  scoped "through <last completed season>", none repeating a bio.
- **`voice.md`** (if the blog is on): the blog's name, editions, title format, draft location,
  author and categories, then the voice from the interview. Copy the section structure of an
  existing one; `docs/writing.md` holds the craft rules every league shares.
- **`NOTES.md`**: the league's facts and quirks for future agents: what the interview settled,
  pipeline warnings explained, anything surprising in the data.
- **`pages`** (optional): page intros in the league's voice.

## 4. Brand

```bash
npm run brand              # tokens, seal, wordmark, ribbon, laurel, icons
npm run smui-theme-light   # rebuild the stylesheet (dev never recompiles Sass)
```

It warns if a colour is too light to read and corrects it. Look at the seal and wordmark in
`static/brand/` in a browser; long names are shrunk to fit. A league that has its own logo puts
SVGs with the same file names in `league/brand/`.

## 5. Preview every page

`npm run dev`, then check each page at desktop and at 375px width, with the console open: home,
matchups, standings, free agents, trades, managers and one manager, rosters, seasons and each
season, Trophy Room, records, rivalry, drafts, Stat Lab, constitution, resources, blog. Every
page loads without errors and nothing scrolls sideways on a phone. History pages show "through
week N" and their empty states make sense for a new league.

## 6. Deploy

Confirm each outward-facing step with the commissioner before doing it.

1. **A GitHub repository** for the site (their account), and push.
2. **Vercel**: import the repository at vercel.com/new; the defaults are right (SvelteKit,
   `npm run build`). No environment variables are needed unless the blog uses Contentful.
3. **Keep the data fresh**: the `refresh-data` GitHub Action runs the pipeline twice a week and
   commits the result once the repository variable `REFRESH_DATA` is set to `true`
   (Settings → Secrets and variables → Actions → Variables). Otherwise run `league-data`'s
   refresh after each week.
4. **A domain** (optional), in Vercel's project settings; then set `siteUrl`.

## 7. Hand over

Tell the commissioner what they have and what keeps it alive:

- Weekly, if the blog is on: `league-recap` (Monday) and `league-preview` (midweek).
- After the title game, and before each new season: `league-season`.
- When someone joins: `python3 scripts/sync-managers.py --photos`, then fill in their details.
