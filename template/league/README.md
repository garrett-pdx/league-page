# `league/`: everything about one league

This directory is the only part of the site a league edits. The rest of the repository is the
engine: it reads this directory and Sleeper, and holds nothing about any particular league.
Updating to a new engine release therefore never conflicts with a league's content.

| File | What it is | Required |
| --- | --- | --- |
| `league.json` | Identity, blog, links, page intros, history before Sleeper, data overrides and managers. Validated against [`schema/league.schema.json`](../schema/league.schema.json), which documents every field. | yes |
| `home.md` | The home page's introduction. Markdown; raw HTML is allowed. | no |
| `constitution.md` | The league's rules. Each `## Heading` becomes a numbered section and each `### Heading` a numbered rule, so the numbering never needs maintaining by hand. Without this file the Constitution page and its nav entry disappear. | no |
| `managers/` | Manager photos, referenced from `league.json` by file name. Square, no larger than 500x500. | no |
| `archive-facts.json` | The Trophy Room's "From the archives" facts (shape documented in `src/lib/History/ArchiveCard.svelte`). Without it the card is hidden. | no |
| `posts/` | Blog posts, when `blog.backend` is `markdown`. | no |

Generated files are not here. `static/data/` (the history dataset) is written by the pipeline
from Sleeper; never hand-edit it.

## Rules

- **Facts come from data.** Every number in a bio, the home page or an archive fact is
  re-derived from `static/data/` when it is written, never typed from memory.
- **Managers are keyed by Sleeper `user_id`**, never by roster ID (roster IDs move between
  seasons) and never by display name (people rename).
- **Photos are served from here**, not hotlinked from Sleeper: a Sleeper avatar URL changes
  whenever its owner changes their avatar. Name a photo after the manager's Sleeper handle, so
  renaming the manager cannot orphan it, and check the file's real format before trusting its
  extension (Sleeper's `Content-Type` header is unreliable).
- **A rival is another manager's `userId`**, or a named rival with a photo
  (`everyone.png` and `question.jpg` are built in).
- **Overrides carry a note.** `overrides.statCorrections` and `overrides.eligibility` exist
  because Sleeper's data occasionally disagrees with itself; the pipeline's self-checks say when
  one is needed, and the note says why it is there.
