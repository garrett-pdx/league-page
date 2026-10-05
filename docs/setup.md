# Setting up a site for your league

Everything about your league goes in `league/`; nothing else needs editing. There are two ways
to get there.

## The quick way: with a coding agent

Open a copy of this repository in [Claude Code](https://claude.com/claude-code) (or any agent
that can follow a Markdown playbook) and say:

> Set up a site for my Sleeper league: https://sleeper.com/leagues/<your league id>

The `league-setup` skill (`.claude/skills/league-setup/SKILL.md`) does the rest: it checks the
engine handles your league, asks you one round of questions (name, colours, history, managers,
rules), builds the dataset, writes `league/`, generates your logo and colours, previews every
page, and walks you through deploying. Keep reading only if you want to do it by hand, or to
understand what it did.

## By hand

You need Node 20 or 22, Python 3.7 or newer, and git.

### 1. Get the code

Use the template on GitHub ("Use this template"), clone your copy, and install:

```bash
npm install
```

### 2. Find your league and try it

Your league ID is the number in `sleeper.com/leagues/<id>` (in the app: league settings, share).
Use the **current season's** league; Sleeper issues a new ID each season.

```bash
scripts/try-league.sh <id>                # the whole data pipeline, in try-league/<id>/
npm run dev:league -- try-league/<id>     # the site for your league, at localhost:5174
python3 scripts/league-summary.py <id>    # your league's format, from Sleeper
```

`try-league.sh` must end with three `ok`s. A `FAIL` means the engine doesn't handle something
about your league; please open an issue with the message. Warnings are normal (see
Troubleshooting).

### 3. Configure

Replace the demo in `league/league.json`. Two fields are required; every field is documented in
`schema/league.schema.json` (editors that understand `$schema` autocomplete it):

```json
{
  "$schema": "../schema/league.schema.json",
  "sleeperLeagueId": "<id>",
  "name": "The Example League"
}
```

Then build the data and fill in the managers:

```bash
python3 scripts/pull-league-history.py
npm run derive-site-data
npm run derive-narratives
python3 scripts/sync-managers.py --photos   # everyone who has held a roster, with their avatar
python3 scripts/suggest-rivals.py --write   # rivals from head-to-head history (optional)
```

Give managers real names, hometowns and bios in `league.json` as your league supplies them.

### 4. Write the league's pages

All optional; a page or section without its file simply doesn't appear.

| File | What |
| --- | --- |
| `league/home.md` | the home page's introduction |
| `league/constitution.md` | your rules: `##` per section, `###` per rule, numbered automatically |
| `league/archive-facts.json` | "From the archives" facts on the Trophy Room |
| `league/voice.md` | the blog's voice, if you'll have an agent write posts |
| `league/NOTES.md` | your league's facts and quirks, for future agents |

`docs/league-lore.md` (written by `derive-narratives`) has a few hundred facts from your league's
history to draw on.

### 5. Your colours and logo

Set `theme` in `league.json` (a dark brand colour and a championship colour):

```json
"theme": { "primary": "#14532d", "trophy": "#d4af37", "tagline": "Dynasty Football" }
```

```bash
npm run brand              # colour tokens, seal, wordmark, ribbon, laurel, icons
npm run smui-theme-light   # rebuild the stylesheet
```

Colours too light to read are darkened automatically, with a warning. To use your own logo, put
SVGs named like the generated ones (`seal.svg`, `seal-simple.svg`, `wordmark.svg`, `banner.svg`,
`laurel.svg`) in `league/brand/` and run `npm run brand` again.

### 6. Preview

```bash
npm run dev
```

Check the pages at desktop and phone width.

### 7. Deploy

1. Push your repository to GitHub.
2. Import it at [vercel.com/new](https://vercel.com/new). The defaults are right; no environment
   variables are needed unless your blog uses Contentful.
3. Keep the history current: set the repository variable `REFRESH_DATA` to `true` (Settings →
   Secrets and variables → Actions → Variables) and the `refresh-data` GitHub Action pulls from
   Sleeper twice a week and commits. Or run step 3's three pipeline commands yourself after each
   week.
4. Add your domain in Vercel, and set `siteUrl` in `league.json`.

## The blog

`blog.backend` in `league.json`:

- **`markdown`** (the default). Posts are files in `league/posts/`, published by committing them:

  ```markdown
  ---
  title: Week 4 preview
  date: 2026-09-30
  type: Preview
  author: <sleeper username>
  featured: true
  ---
  The post, in markdown. Tables, lists and links all work.
  ```

  `node scripts/publish-article.mjs <draft.md> --type Recap --author <username>` turns a draft
  whose first line is `# Title` into a post file. The `league-recap` and `league-preview` skills
  write, fact-check and publish weekly posts.
- **`contentful`**: posts from a Contentful space. Set `VITE_CONTENTFUL_SPACE` and
  `VITE_CONTENTFUL_CLIENT_ACCESS_TOKEN` (the read-only delivery token) in Vercel, and
  `blog.contentful.postType` to your content type's ID. Publishing from the command line needs a
  management token as `CONTENTFUL_MANAGEMENT_TOKEN` in a local `.env` only — never a `VITE_`
  variable and never in Vercel.
- **`none`**: no blog; the tab disappears.

## Every season

After the title game, and again when Sleeper renews your league for a new season, follow the
`league-season` skill. The step people forget: the new season has a new league ID.

```bash
python3 scripts/find-current-league.py --write
```

## Updating

When the footer says a newer version is available:

```bash
python3 scripts/update-engine.py   # the latest engine; or pass a tag, e.g. v1.2.0
git diff                          # review
npm install && npm run smui-theme-light
```

It replaces the engine's files and never touches `league/`, your data, or your generated brand.
Read the CHANGELOG for anything that needs a step from you, then commit.

## Troubleshooting

- **Pipeline warnings** ("disagreement with Sleeper's settled figures") mean Sleeper's own
  records and its weekly scores disagree slightly, almost always because of a stat correction
  after a week settled, or a player whose position has changed since. The site is fine. Each
  warning prints the `league.json` override that would silence it.
- **A pipeline failure** writes nothing and leaves the last good data in place. Read the
  message; if it looks like a format the engine doesn't handle, open an issue.
- **`npm run build` fails locally on Node 23 or newer** (the Vercel adapter refuses it). Vercel
  is unaffected; to build locally use `DOCKER_BUILD=true npx vite build`.
- **Colours didn't change**: `npm run dev` doesn't recompile Sass; run `npm run smui-theme-light`.
