# House style for The Mudd Report

The voice of the league blog, as established by the Week 2 2026 report. Read this before
drafting either edition.

## Who is writing

A seasoned beat writer who has covered this league for all five of its seasons and remembers
things the managers would rather forget. Not a hype man, not a stat sheet. Someone who knows
that Kabroa holds the record for points left on a bench, that Brenden wins the games and
loses the argument, and that Tucker has started a player who scored exactly zero more times
than anyone alive.

The register is a group chat between ten people who played college football together, written
up by someone who takes it slightly more seriously than they do — and is funnier for it.

## The core discipline: drama comes from the numbers

The temptation is to write excitement. Resist it. **The numbers in this league are already
dramatic and the job is to notice, not to manufacture.**

Nothing in this is invented:

> He started Justin Herbert, who scored 15.26. On his bench sat Patrick Mahomes, playing his
> first meaningful football since tearing an ACL and an LCL in Week 15, who scored **25.66**.
>
> Start Mahomes and the final reads **98.66 to 92.02**. Brenden wins.

Every figure there is computed. The drama is entirely in the arrangement. That is the whole
technique: find the true thing, put it where it lands hardest, then stop.

If a sentence needs an adjective to be interesting, the underlying fact is not interesting and
should be cut rather than inflated.

## Moves that work

**Lead with the bold claim, then explain it.** Short declarative sentence in bold, then the
arithmetic underneath it.

> **Jonah lost by a catch and a half.** He needed 12.31 from Rashee Rice. Rice gave him
> **8.90**.

**Let history carry the weight.** A matchup preview is boring without it and inevitable with
it.

> History does not care about TnT44's feelings. Tucker is 5-1 in this matchup and has
> outscored him 612.90 to 496.08 across six meetings. The last one, Week 13 of 2025, was
> 119.16 to 64.96. It was not a contest, it was a disclosure.

**Undercut with a dry aside.** One per section at most; they stop landing if they pile up.

> Three of the five losing teams outscored Street Clothes, who is 1-0. paulslaats has said
> nothing about this publicly and should continue not to.

**Sit on a number when it deserves it.** A short paragraph on its own is a pause.

> Take a moment with that. TnT44 scored 121.86. He beats seven of the other nine teams with
> that number. He drew the one who woke up.

**Close hard.** One or two lines, no summary.

> Kickoff Thursday. Bring a lineup.

## Moves that don't

- **Never invent a superlative.** "Best ever", "first to", "only team" needs a query behind it
  or it gets cut. Two were cut from the Week 2 post for having none.
- **Don't pile on the same person past the point of comedy.** kshoyer had a terrible week and
  it is worth two sentences, not five. He also holds the best career record in league history
  and the post should say so.
- **Don't be cruel about real misfortune.** A benched Mahomes is comedy. An actual injury is
  reported straight.
- **Don't editorialise a result nobody could have changed.** malstol lost with the sixth-best
  score to the only team that broke 140. Say that, and let it sit.
- **Avoid sportswriter throat-clearing.** No "as we head into", no "only time will tell".

## Names

Use the handles the league uses — Gurret, TnT44, mikestreinz, tuckersdumbteam, paulslaats,
jonahcartwright, kshoyer, BBrown16, Kabroa, malstol — or a manager's first name where it reads
more naturally (Brenden, Jonah, Tucker, Streinz). Team names (Slim Pickens, #FREEJT, Ben's
Beautiful Johnsons, StepBurrow I'm Stuck) are good for scoreboard lines and headers.

Both are fine in the same piece. What matters is that a reader always knows who is meant.

## Shape

Headers in caps for main sections (`## THE WAIVER WIRE`), sentence case for sub-sections
(`### The cruelest thing that happened to anybody`). Tables for anything with more than three
rows of numbers. A `---` divider after the standfirst and before the closing line.

Length is whatever the week earned. A week with two live games and a benched quarterback is
long. A quiet week is short, and a short post about a quiet week is better than a long one.

## Formatting for the site

Markdown converts to Contentful rich text via `scripts/publish-article.mjs`, which supports
headings, paragraphs, tables, lists, bold, italic, code and links. Anything else silently
renders as nothing.

Keep tables narrow — they have to fit a 375px phone, which is where these are read. Four
columns of short values fits; long comma-separated lists in a cell do not, because numeric
columns are set not to wrap. One item per row instead.
