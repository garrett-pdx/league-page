<div align="center">
  <img alt="Fantasy Football Website with History" src="static/brand/wordmark.svg" width="320px" />

# Fantasy Football Website with History

**A website for your Sleeper fantasy football league, with its whole history in it.**

Live standings, matchups and rosters, plus every past season, the records, the rivalries, the
lore and a weekly blog — in your league's colours, set up from a league ID.

Live example: **[muddleague.site](https://muddleague.site)**

</div>

---

## What your league gets

- **This week:** matchups with live scores, standings (divisions, ties and median games when your
  league has them), power rankings, rosters, trades and waivers, and a free-agent search by
  depth-chart slot.
- **Every season, back to the first:** a page per season with the final table, the bracket, the
  champion's run, the draft and keepers, the trades, and the best and worst weeks — including
  seasons played before Sleeper.
- **Records and Stat Lab:** highs, lows, close calls and rankings, and a sortable, chartable lab
  over every game ever played, with the view kept in the link so it can go in the group chat.
- **A Trophy Room** with a Hall of Fame and facts from the archive; **rivalries** with a
  head-to-head grid; **manager pages** with career records and finishes.
- **Lore:** a few hundred verified facts about your league, generated from its history, for bios,
  posts and trash talk.
- **A blog** that an AI agent can write every week — a Monday recap and a midweek preview — from
  your league's own numbers, fact-checked before it publishes. Posts are just Markdown files.
- **Your league's look:** colours, a seal, a wordmark and icons generated from two colours.
- **A constitution** page built from your rules, numbered automatically.

It handles any Sleeper league format: redraft, keeper or dynasty; superflex, IDP, kickers and
defenses; any team count and playoff size, byes, two-week rounds, consolation brackets and toilet
bowls; median games; divisions; orphaned teams; and a league in its very first season.

## Set it up

**With a coding agent (recommended).** Click "Use this template", open your copy in
[Claude Code](https://claude.com/claude-code), and say:

> Set up a site for my Sleeper league: https://sleeper.com/leagues/<your league id>

The `league-setup` skill checks your league, asks you one round of questions, builds the data,
writes your league's pages, generates your colours and logo, previews everything and walks you
through deploying on Vercel. Other agents can follow the same playbooks in
[`.claude/skills/`](.claude/skills/) (see [AGENTS.md](AGENTS.md)).

**By hand.** [docs/setup.md](docs/setup.md) walks through every step. The short version:

```bash
npm install
scripts/try-league.sh <league id>              # does the engine handle your league?
# replace the demo in league/: a league.json with just your ID and name (docs/setup.md), then:
python3 scripts/pull-league-history.py && npm run derive-site-data && npm run derive-narratives
python3 scripts/sync-managers.py --photos
npm run brand && npm run smui-theme-light
npm run dev
```

## How it works

Everything about one league lives in [`league/`](league/): a config file (documented field by
field in [`schema/league.schema.json`](schema/league.schema.json)), Markdown for the home page,
the constitution and the blog's voice, manager photos, and posts. Everything else is the engine,
which you never edit for your league — so updating to a new release
(`python3 scripts/update-engine.py`) never conflicts with your content.

Live pages read Sleeper's public API directly. History pages read a dataset built offline by a
small Python pipeline (standard library only) that pulls every season from Sleeper, then checks
its own work against Sleeper's records before writing anything. A GitHub Action can run it twice
a week. The site is SvelteKit, deployed on Vercel.

This repository's own `league/` holds a demo league: a real Sleeper league with neutral content.

## Credits

Built on [League Page](https://github.com/nmelhado/league-page) by Nicholas Melhado and its
contributors, which this project began as a fork of. MIT licensed; see [LICENSE](LICENSE).

Not affiliated with Sleeper.
