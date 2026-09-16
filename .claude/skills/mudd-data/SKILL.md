---
name: mudd-data
description: Refresh the Mudd League dataset from Sleeper and produce the verified fact block for a week — scores, optimal lineups, benched points, efficiency, all-play records, rankings, head-to-head history and all-time leaderboards. Use this whenever you need current league numbers for any reason: before writing or publishing any league post, when asked "who's winning", "what did X score", "how many points did Y leave on the bench", "what's the head-to-head between A and B", "is that a record", or when league data looks stale. Also use it after a week completes to commit the refreshed dataset. Both mudd-monday and mudd-preview depend on this skill; run it first rather than querying Sleeper ad hoc.
---

# Mudd League data

Everything a post asserts has to come from here. The league's own notes call this the hard
rule (`docs/post-generator-skill.md`), and it has a second half that matters just as much:
**re-derive at publish time**, because a number that was true when it was written is not the
same thing as a number that is true.

## The fact block

```bash
python3 scripts/week-facts.py <week>              # human-readable table
python3 scripts/week-facts.py <week> --json       # machine-readable
python3 scripts/week-facts.py <week> --live       # also flag starters yet to play
```

For each team it computes scored, optimal, benched, efficiency, all-play record and score
rank; for each game the margin, the winner, and what a trailing team still needs; plus the
top started performances. Season defaults to Sleeper's current one.

The all-play record — what you'd be if you played everyone that week — is the number that
separates *beaten* from *unlucky*, and it is most of what a weekly post argues about.

## History and fact-checking

```bash
python3 scripts/week-facts.py --h2h Gurret mikestreinz
python3 scripts/week-facts.py --history
```

`--history` prints all-time leaderboards: highest scores, **highest losing scores**, lowest
scores, most points benched, closest finishes. Check every superlative against it. A claim
that something is the best or worst ever is the easiest kind of sentence to write and the
easiest to get wrong — "the best losing score in league history" turned out to be fourteenth.

`--h2h` gives the record, total points each way and every meeting, including playoffs.

## Refreshing the committed dataset

```bash
python3 scripts/pull-league-history.py    # rewrites static/data/*.json
npm run derive-narratives                 # rebuilds narratives.json + docs/league-lore.md
```

Run the puller after a week completes and commit the diff — it also picks up in-season
rookies, who are otherwise missing from `players.json` and would print as raw ids. It is not
needed just to write a post: `week-facts.py` reads live Sleeper for the current week and only
uses the committed files for history.

## Traps this data has already sprung

These each produced a wrong published fact once. They are handled in the scripts, but you
will meet them again if you query Sleeper directly.

- **A scheduled-but-unplayed season looks completely real.** Once Sleeper publishes a
  schedule, every week returns ten rosters, eight starters and genuine non-zero `matchup_id`s
  with every score `0.0`. Testing `if WEEKS[season]` lets it through. `season_played()`
  requires a point to have actually been scored.
- **Every season carries a fictional week 18** with `matchup_id: 0` and no lineups set. Treat
  falsy `matchup_id` as "no fixture".
- **Keepers occupy draft slots.** Draft steals and busts must filter `is_keeper` or they
  retell last year's keeper decision as this year's draft pick.
- **Roster shape changes between seasons** — 14 spots in 2025, 13 in 2026. Optimal-lineup maths
  reads `roster_positions` per season rather than assuming.
- **`players.json` only holds players who have appeared in league history.** New signings and
  rookies fall back to the live `/players/nfl` dictionary (~5MB, so only when needed).

## Reading "who is still playing"

`--live` flags starters currently sitting on exactly 0.0. That is a heuristic, not a fact:
it cannot distinguish a player whose game has not kicked off from one who genuinely scored
nothing. Confirm against the actual NFL schedule before writing that somebody is "still
alive", and say which game they are in.
