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
| 1 | **A. The nav**, plus the voted 2026 roster-change text (F) | Every page benefits; the new pages need its groups; the roster text is wrong on the live site today | done |
| 2 | **C1–C3.** Records, Matchups, Standings readable on phones; creates `src/theme/_site.scss` | The worst phone problems, on the most-used pages | pending |
| 3 | **History step 0 + 1.** The game table, then schedule luck on Standings | Foundation for four pages; most useful mid-season | step 0 running in parallel (worktree) |
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

### Step 1: nav and roster text (done, Opus, about 21 minutes)

Commits `3e70099`..`0674023`, 13 files. The node-adapter build passes.

- **Top bar:** Managers, Matchups, Standings, Free Agents, Trades & Waivers, Blog, League ▾.
  - Home is dropped.
  - Tab padding is 12px between 951px and 1100px so all seven tabs fit (885px).
- **League menu:** grouped into This Season, History and Rules & Tools. Off-site links show ↗.
- **Highlight** follows client-side navigation. /manager lights Managers. Each dropdown item is
  marked when it's the current page.
- **Tab titles** match the nav labels. Manager pages show the manager's name; blog posts show
  the post title.
- **Phone menu:**
  - a real 44px button;
  - items at 7.46:1 contrast and 44px tall;
  - a sticky 61px bar on phones only.
- **Roster change:** five bench spots and thirteen rounds, with an amendment note in the
  constitution.

**Changes to the remaining plan:**
- **Sticky bar offset.** Anything that sticks or jumps to an in-page anchor on phones must
  allow for the 61px bar. Steps 2, 4 and 6 carry this.
- **Footer links** are 37px tall: added to C5 (step 6).
- **Layout shift** measured 0.72 on /standings at 375px: B3 (step 4) owns it.
- **The blog can't be checked locally:** there's no Contentful token in `.env`. Check B4's
  blog typography by reading the code, or against the live site.
- **New pages in the nav:** Seasons and Stat Lab go under `{ group: 'History' }`. Titles and
  highlighting then work automatically, through a first-segment fallback.
- **Dropdown accessibility.** The desktop dropdown's items stay in the DOM while hidden, which
  predates this work. Possibly reachable by screen readers. Added to step 10's audit.
