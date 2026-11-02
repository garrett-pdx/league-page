---
name: league-monday
description: Draft a Monday edition — the in-progress weekly recap written before Monday Night Football — for any Sleeper fantasy league in scripts/leagues.json, starting with BPM Fantasy Football. Covers the weekend's results, team of the week, lineup efficiency, benched points, schedule luck, injuries and who is still alive in the Monday game, with teams called by their Sleeper team names. Use whenever asked for a Monday post, recap or "write up this week" for BPM or any league other than the Mudd League, or when asked to run the Monday article for "the other league" or "both leagues". For the Mudd League's own blog post use mudd-monday, which this generalizes; it publishes to Contentful and leans on Mudd's committed dataset.
---

# Monday edition — any league

The `mudd-monday` skill, generalized. Everything that makes that post good applies here: read
its "What makes this edition land" and "Before publishing — the checks" sections before
drafting. The differences are where the numbers come from, what the teams are called, the
voice, and where the draft goes.

**The hook is the same: the week is not over.** Some games are decided, some are not, and
specific teams are sitting on specific players who can still change their week.

## Which league

`scripts/leagues.json` maps a short name to a Sleeper league ID and a naming rule:

| name | league | teams called by |
|---|---|---|
| `bpm` | BPM Fantasy Football (16 teams) | Sleeper team name |
| `mudd` | The Mudd League | handle — but use `mudd-monday` for Mudd |

A league not listed works by raw league ID (`--league 1389691887358586880`); add it to the
file once it becomes a regular. For "both leagues", run `mudd-monday` for Mudd and this for
the rest.

## The numbers: `scripts/league-week.py`

Everything is read live from Sleeper; the league needs no committed dataset.

```bash
python3 scripts/league-week.py --league bpm <week>            # the fact block
python3 scripts/league-week.py --league bpm <week> --json     # every field, incl. lineups
python3 scripts/league-week.py --league bpm --history         # all-time leaderboards
python3 scripts/league-week.py --league bpm --standings       # this season, completed weeks
python3 scripts/league-week.py --league bpm --h2h "Team A" "Team B"
python3 scripts/projections.py <week> "Player" "Player" --league bpm
```

The current NFL week is `https://api.sleeper.app/v1/state/nfl` — check it rather than
assuming: on Monday 2 November 2026 the user asked for "week 9" and it was week 8.

**What it settles that `week-facts.py` leaves to you.** Each starter is classified from
Sleeper's week data, so a 0.0 is no longer ambiguous:

- `pending` — his NFL team has a game this week and hasn't played it. He is still live.
- `bye` — his team has no game. Starting him was a lineup decision.
- `inactive` — his team played, he didn't dress. Also a lineup decision, and usually the
  story: check when he was ruled out before saying the manager should have known.
- `played` — a real zero.

`fin.bench` / `fin.eff` grade only finished slots. Publish those, not the raw figures, for
any team with a starter still to play; bench players still to play aren't counted either,
and the table should say so. The tool's game states are `FINAL`, `LIVE`, and
`DECIDED, LEADER STILL PLAYING` — a leader on a thin margin with a starter to come can
still lose it to a negative score (a lost fumble), so call that one "leading", not "won".

**Run it before Monday's kickoff, or after the game ends.** A player in a game in progress
has recorded a game and counts as `played`, so a mid-game run understates what's to come.

**History is regular season only**, every season reachable through `previous_league_id`, and
labelled with each manager's *current* team name (a departed manager shows their handle). So
"Team Regina Jackson's 173.54 in 2022" means that manager's team in 2022, under whatever it
was called then; write "tristanvr's team" or name the season if that matters. Playoff and
consolation games are not in it, so "highest score ever" from it means regular season; say so.

## Names

Teams are their **Sleeper team names**, read live on every run — the BPM Week 2 2026 article
used three names the teams had already dropped, because they had been cached a week earlier.
The handle is in the JSON (`handle`) for disambiguation. Never carry a team name over from an
earlier post or from memory.

**Managers are "they/them" and "the manager", never "he" or "his"** — nobody in these
leagues has stated their pronouns, and a handle doesn't tell you. NFL players keep their own
pronouns.

## Shape for a big league

BPM has sixteen teams and eight games. The rule from the laptop folder's notes: **every team
gets a real mention, not just a table row.** That makes the scoreboard the backbone — one
bold line and one true sentence per game — and it is why the post may run longer than
Mudd's: aim for about **1,400 words of prose**, tables not counted
(`python3 scripts/reading-time.py <file>`). Keep tables to four columns.

```
# <LEAGUE> — WEEK N RECAP
*Monday <date> · written before <Monday game> · <n> of <m> games final · <N> min read*

## THE SCOREBOARD          one bold line per game: FINAL / LIVE / leading; one sentence each
## TEAM OF THE WEEK — <team>
## THE LOWLIGHT REEL       bye and inactive starters, the costliest benchings (projections first)
## LINEUP EFFICIENCY       team / bench / eff%, worst last, finished slots only
## SCHEDULE LUCK           all-play table; ROBBED and GOT AWAY WITH IT
## THE INJURY WARD         searched and attributed news only
## STILL ALIVE TONIGHT — <game, time>
---
<closing line>
```

Drop any section the week didn't earn.

## The checks (from mudd-monday — all of them still apply)

- **Every superlative** against `--history`, counting from the full output, and scoped
  ("regular season", "since 2022").
- **Projections before blame** (`projections.py --league ...`): a start/sit call that
  followed Sleeper's projections is bad luck, not a mistake.
- **Tense pass**: list every game the draft calls over and confirm its trailer has nobody
  left — and that the leader has no one who could go negative on a sub-two-point margin.
- **Numbers pass**: re-run the fact block right before handing the draft over; check every
  table cell, score, and started-versus-benched claim.
- **Names pass**: every team name in the draft appears verbatim in this run's output.
- **Repetition**: `python3 scripts/repeat-check.py docs/<league>/articles/<draft>.md`
  compares against the previous two posts *in the same folder*. A story gets one full
  telling. Posts written elsewhere (the laptop's `~/Desktop/fantasy leagues 2026/` folder)
  are invisible to it until they're copied in.

## Where the draft goes

`docs/<league>/articles/<season>-w<week>-monday.md`, e.g. `docs/bpm/articles/2026-w8-monday.md`.
League-specific voice notes live in `docs/<league>/voice.md`; read it first. There is no
publisher for these leagues: the draft is the deliverable. Commit it, and hand the user the
file. `publish-article.mjs` is Mudd's Contentful blog only — never point it at another league.
