# Site revamp: order and log

Started 2026-10-02 on the local branch `site-revamp`. Nothing gets pushed until Garrett has
reviewed it; every push to `master` deploys.

The plans being carried out:
- [`plan-site-todo.md`](plan-site-todo.md): workstreams A–F
- [`plan-history-pages.md`](plan-history-pages.md): History steps 0–4
- [`site-todo.md`](site-todo.md): the list both plans come from

## Order

| Step | Work | Why here | Status |
| --- | --- | --- | --- |
| 1 | **A. The nav**, plus the voted 2026 roster-change text (F) | Every page benefits; the new pages need its groups; the roster text is wrong on the live site today | pending |
| 2 | **C1–C3.** Records, Matchups, Standings readable on phones; creates `src/theme/_site.scss` | The worst phone problems, on the most-used pages | pending |
| 3 | **History step 0 + 1.** The game table, then schedule luck on Standings | Foundation for four pages; most useful mid-season | pending |
| 4 | **B1–B3.** `PageHeader` on every page, text fixes, the page jumping as it loads | History pages reuse `PageHeader` | pending |
| 5 | **D.** Links between pages, plus **History step 2**, the head-to-head grid | Both work on Rivalry and manager links | pending |
| 6 | **C4–C5 + B4–B5.** Drafts, remaining small text and tap targets, blog typography, desktop layouts | Polish on less-used pages | pending |
| 7 | **E. Content:** bio typos and league lines, home page copy, Resources, countdown | Writing, once the page frames are settled | pending |
| 8 | **History step 3.** Seasons archive | Biggest new page | pending |
| 9 | **History step 4.** Stat Lab, first release | Built on everything above | pending |
| 10 | **F wrap-up.** `CLAUDE.md` corrections, end-of-season checklist, `mudd-preview` post type, full-site audit | Docs describe the finished state | pending |

## Decisions already made (2026-10-02)

- The 2026 roster change was **voted 7–3**: five bench spots, thirteen roster spots, a
  thirteen-round draft.
- Drop the Home tab. Follow the plan's other nav recommendations.
- The constitution's missing rules are dropped; don't invent rules.
- Move the news feed to the bottom of Resources.
- Leave "Marvey Mudd" (Malcolm's bio) and the Tucker and Kevin bio questions alone.
- The home page copy is written by the step-7 agent and reviewed by Garrett before any push.

## Log

_Each step adds what was done, what was found, and any changes to the remaining plan._
