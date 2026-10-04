# Writing the league blog

The craft rules for every post the recap and preview skills write, for any league. The league's
own voice (who is writing, how people are named, running bits, the blog's name and title
format) lives in `league/voice.md`; read both before drafting.

These rules were learned the hard way, on a real league's blog, one wrong post at a time.

## The core discipline: drama comes from the numbers

The temptation is to write excitement. Resist it. The numbers in a fantasy league are already
dramatic, and the job is to notice, not to manufacture.

Nothing in this is invented:

> He started Justin Herbert, who scored 15.26. On his bench sat Patrick Mahomes, playing his
> first meaningful football since tearing an ACL, who scored **25.66**.
>
> Start Mahomes and the final reads **98.66 to 92.02**. He wins.

Every figure there is computed. The drama is entirely in the arrangement: find the true thing,
put it where it lands hardest, then stop. If a sentence needs an adjective to be interesting,
the fact under it is not interesting and should be cut rather than inflated.

## Moves that work

**Lead with the bold claim, then explain it.** A short declarative sentence in bold, then the
arithmetic underneath.

> **He lost by a catch and a half.** He needed 12.31 from his receiver. He got **8.90**.

**Let history carry the weight.** A matchup preview is a schedule without it and inevitable
with it: the record, the margins, the last meeting.

> History does not care about his feelings. His opponent is 5-1 in this matchup and has
> outscored him 612.90 to 496.08 across six meetings. The last one was 119.16 to 64.96. It
> was not a contest, it was a disclosure.

**Undercut with a dry aside.** One per section at most; they stop landing if they pile up.

**Sit on a number when it deserves it.** A short paragraph on its own is a pause.

> Take a moment with that. He scored 121.86, which beats seven of the other nine teams. He drew
> the one who woke up.

**Close hard.** One or two lines, no summary.

## Moves that don't

- **Never invent a superlative.** "Best ever", "first to", "only team" needs a query behind it
  or it is cut, not softened.
- **Don't pile on one person past the point of comedy.** A terrible week is worth two
  sentences, not five, and the post should say what is going right for them too.
- **Don't be cruel about real misfortune.** A benched star who goes off is comedy. An injury is
  reported straight.
- **Don't editorialise a result nobody could have changed.** Losing with the week's
  sixth-best score to the only team that broke 140: say that, and let it sit.
- **No sportswriter throat-clearing.** No "as we head into", no "only time will tell".
- **Don't call a sensible decision a mistake.** The optimal lineup is hindsight. Before mocking
  a start/sit call, check what Sleeper projected for both players that week
  (`scripts/projections.py`). If the manager started the projected pick, the story is that he
  did the right thing and lost anyway, and it is usually the better story. Never cite preseason
  ranks; "ranked 48th in August" says nothing about the week in question.
- **Don't let history read as news.** A fact about a past meeting names the year and the
  pairing. "The three highest scores in league history were all posted in fixtures being
  played this week" reads as though they happened this week.
- **Don't re-tell what the last post told.** Most readers read every edition. A story gets one
  full telling; a recurring section that re-covers the previous post is the worst version of
  the problem. If a past result changes a story going forward, it gets one clause inside it.
- **Don't reuse a device every week.** "Start X and the final reads A to B" is the best move in
  the book and dies if it is in every section of every post: once per post. Sub-headings are
  fresh each week even where the section is fixed.
- **Running bits advance; they don't recap.** Each week adds the new week's row and a new joke,
  and keeps the backstory to a table.
- **Don't say a live result is settled.** "Won", "has the record", "team of the week" all wait
  for the last player to finish. Until then: leading, on course, could.

## Shape

Title, then an italic dateline (`*<day> <date> · <status> · <N> min read*`), then straight into
the first section. No standfirst: the dateline and the first section already say what the week
was. Main section headers in caps, sub-sections in sentence case. Tables for anything with more
than three rows of numbers. A `---` divider before the closing line. Drop any section the week
didn't earn.

**Aim for a five-minute read**: about 1,150 words of prose at most; tables don't count. That is
a ceiling, not a quota. The cuts that cost least: a standfirst, a second sentence restating the
first, minor waiver moves, a paragraph whose point is already in a table. The cuts that cost
most: the one dry aside per section, and the specific number that makes a claim land.

**Tables: four columns at most**, short values, one item per row. They have to fit a 375px
phone, which is where these are read; numeric columns do not wrap.

## Formatting

Markdown: headings, paragraphs, tables, lists, bold, italic, code and links. The markdown blog
renders all of it (and raw HTML); the Contentful backend converts only those node types, and
anything else silently renders as nothing there.
