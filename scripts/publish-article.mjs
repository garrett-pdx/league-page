/**
 * Publish a Markdown article to the league's blog.
 *
 * With blog.backend "markdown" (league/league.json) the post is written to league/posts/<slug>.md
 * with its frontmatter, and committing that file is what publishes it -- the next deploy serves
 * it. With "contentful" it is converted to Contentful Rich Text and created (or updated) as an
 * entry, as described below.
 *
 * Contentful's `body` is a Rich Text field, which is a structured node tree rather than a
 * string -- pasting Markdown into it produces literal asterisks and pipes, and rebuilding a
 * four-column table by hand in their editor is miserable. This converts Markdown to the Rich
 * Text document shape and creates the entry directly.
 *
 * THE TOKEN IS DELIBERATELY NOT NAMED VITE_ANYTHING.
 *
 * Writing to Contentful needs a *management* token, which has full write access to the space.
 * Vite treats the VITE_ prefix as "expose this to the browser", so a management token under
 * that name is one careless import away from shipping write access to every visitor. This
 * script is run by hand from a terminal and never by the site, so it reads
 * CONTENTFUL_MANAGEMENT_TOKEN from a local, gitignored .env. Do not add it to Vercel: nothing
 * deployed writes to Contentful (comments are off -- see enableComments in leagueInfo.js).
 *
 * Only the node types the site can actually render are emitted -- see generateParagraph() in
 * helperFunctions/getBlogPosts.js, which understands headings, paragraphs, tables, lists,
 * blockquote, hr, hyperlinks, and the bold/italic/underline/code marks. Anything else would
 * round-trip into Contentful and then render as nothing.
 *
 * Usage:
 *   node scripts/publish-article.mjs <file.md> --type Recap --author <sleeper username> [--featured]
 *   node scripts/publish-article.mjs <file.md> ... --date 2026-09-30   # markdown: the post's date
 *   node scripts/publish-article.mjs <file.md> ... --dry-run           # show it, publish nothing
 */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import contentful from "contentful-management";

const ROOT = path.dirname(path.dirname(fileURLToPath(import.meta.url)));

// ---------------------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------------------

function loadEnv() {
  const envPath = path.join(ROOT, ".env");
  const out = {};
  if (fs.existsSync(envPath)) {
    for (const line of fs.readFileSync(envPath, "utf8").split("\n")) {
      const m = line.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$/);
      if (m) out[m[1]] = m[2].replace(/^["']|["']$/g, "");
    }
  }
  return { ...out, ...process.env };
}

// ---------------------------------------------------------------------------------------
// Markdown -> Contentful Rich Text
// ---------------------------------------------------------------------------------------

const text = (value, marks = []) => ({
  nodeType: "text",
  value,
  marks: marks.map((type) => ({ type })),
  data: {},
});

/**
 * Inline parser: bold, italic, code, links.
 *
 * Ordered so `**bold**` is consumed before `*italic*` -- matching italic first would eat the
 * first asterisk of every bold run and leave stray ones in the output.
 *
 * Emphasis recurses, which is not a nicety. This article's standfirst is one long italic run
 * containing `code` spans; parsing only the outer run left the backticks as literal characters
 * inside the italic text, so the published page would have shown them. Marks accumulate down
 * the tree because Rich Text carries them as a list on the leaf text node rather than by
 * nesting elements the way HTML does.
 */
function parseInline(raw, inherited = []) {
  const nodes = [];
  const pattern = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\[[^\]]+\]\([^)]+\))/g;
  let last = 0;
  let m;
  while ((m = pattern.exec(raw)) !== null) {
    if (m.index > last) nodes.push(text(raw.slice(last, m.index), inherited));
    const tok = m[0];
    if (tok.startsWith("**")) {
      nodes.push(...parseInline(tok.slice(2, -2), [...inherited, "bold"]));
    } else if (tok.startsWith("`")) {
      // Code is a leaf: backticks suppress further markup in Markdown.
      nodes.push(text(tok.slice(1, -1), [...inherited, "code"]));
    } else if (tok.startsWith("[")) {
      const lm = tok.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
      nodes.push({
        nodeType: "hyperlink",
        data: { uri: lm[2] },
        content: parseInline(lm[1], inherited),
      });
    } else {
      nodes.push(...parseInline(tok.slice(1, -1), [...inherited, "italic"]));
    }
    last = m.index + tok.length;
  }
  if (last < raw.length) nodes.push(text(raw.slice(last), inherited));
  return nodes.length ? nodes : [text("", inherited)];
}

const paragraph = (raw) => ({
  nodeType: "paragraph",
  data: {},
  content: parseInline(raw),
});

const cell = (raw, header) => ({
  // Rich Text requires block content inside a cell, so the text is wrapped in a paragraph.
  // The site renders it without <p> because genElementStart is called with indent=false there.
  nodeType: header ? "table-header-cell" : "table-cell",
  data: {},
  content: [paragraph(raw)],
});

function tableNode(lines) {
  const split = (line) =>
    line
      .trim()
      .replace(/^\||\|$/g, "")
      .split("|")
      .map((s) => s.trim());

  // Row 2 of a Markdown table is the |---|---| separator, which carries no content.
  const rows = lines.filter((l) => !/^\s*\|?[\s:-]*\|[\s:|-]*$/.test(l));
  return {
    nodeType: "table",
    data: {},
    content: rows.map((line, i) => ({
      nodeType: "table-row",
      data: {},
      content: split(line).map((c) => cell(c, i === 0)),
    })),
  };
}

function markdownToRichText(md) {
  // Soft-wrapped source lines are joined back into one logical line per block; a hard line
  // break inside a Markdown paragraph is not a break in the rendered output.
  const blocks = md.split(/\n\s*\n/);
  const content = [];
  let title = null;

  for (const rawBlock of blocks) {
    const block = rawBlock.trim();
    if (!block) continue;

    const lines = block.split("\n");

    if (/^\|/.test(lines[0])) {
      content.push(tableNode(lines));
      continue;
    }

    if (/^-{3,}$/.test(block)) {
      content.push({ nodeType: "hr", data: {}, content: [] });
      continue;
    }

    const heading = block.match(/^(#{1,6})\s+(.*)$/s);
    if (heading) {
      const level = heading[1].length;
      const label = heading[2].replace(/\n/g, " ").trim();
      // The h1 is the article title, which is its own Contentful field. Emitting it into the
      // body too would render the title twice on the post page.
      if (level === 1 && title === null) {
        title = label;
        continue;
      }
      content.push({
        nodeType: `heading-${level}`,
        data: {},
        content: parseInline(label),
      });
      continue;
    }

    if (/^[-*]\s+/.test(lines[0])) {
      content.push({
        nodeType: "unordered-list",
        data: {},
        content: lines.map((l) => ({
          nodeType: "list-item",
          data: {},
          content: [paragraph(l.replace(/^[-*]\s+/, ""))],
        })),
      });
      continue;
    }

    content.push(paragraph(lines.join(" ")));
  }

  return { title, document: { nodeType: "document", data: {}, content } };
}

// ---------------------------------------------------------------------------------------

function arg(flag, fallback = null) {
  const i = process.argv.indexOf(flag);
  return i > -1 && process.argv[i + 1] && !process.argv[i + 1].startsWith("--")
    ? process.argv[i + 1]
    : fallback;
}

/*
The post's URL slug: /blog/2026-week-4-preview rather than /blog/<Contentful entry id>.

Derived from the file name's season and the title, minus the series prefix: "THE MUDD REPORT —
WEEK 4 PREVIEW" in 2026-w4-preview.md (blog.title is the prefix) becomes 2026-week-4-preview. The year is always in it, so
next season's Week 4 preview can't collide with this one. --slug overrides the derivation.

A slug is set ONCE. Updates keep whatever slug the entry already has, even if the title changes,
because a slug is a URL people have shared; deriving it afresh on every publish would break
every link the first time a post was renamed (two already have been).
*/
// The site's public address and the blog's name (the series prefix a title starts with) come
// from league/league.json.
// LEAGUE_CONFIG points it at another league's league.json, as it does the Python scripts.
const CONFIG_PATH = process.env.LEAGUE_CONFIG || path.join(ROOT, "league", "league.json");
const LEAGUE = JSON.parse(fs.readFileSync(CONFIG_PATH, "utf8"));
const SITE = (LEAGUE.siteUrl || "").replace(/\/$/, "");
const escapeRegExp = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const SERIES_PREFIX = new RegExp(`^${escapeRegExp(LEAGUE.blog?.title || "Blog")}\\s*[—–-]\\s*`, "i");

// Contentful's content type ID for a post (Contentful derives it from the display name).
const POST_TYPE = LEAGUE.blog?.contentful?.postType || "blog_post";

/*
The markdown backend: the article becomes league/posts/<slug>.md, frontmatter first, with its
"# Title" line moved into the frontmatter. Re-publishing the same slug overwrites the file, which
is the update. Nothing is sent anywhere: commit and push the file to publish it.
*/
function publishMarkdown({ md, title, type, author, featured, slug, dryRun }) {
  const date = arg("--date") || new Date().toISOString().slice(0, 10);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) {
    console.error(`bad --date "${date}" -- use YYYY-MM-DD`);
    process.exit(1);
  }
  const body = md.replace(/^\uFEFF/, "").replace(/^\s*#\s+.+\n+/, "");
  const quoted = (v) => (/[:#"']/.test(v) ? JSON.stringify(v) : v);
  const front = [
    "---",
    `title: ${quoted(title)}`,
    `date: ${date}`,
    `type: ${quoted(type)}`,
    `author: ${quoted(author)}`,
    ...(featured ? ["featured: true"] : []),
    "---",
    "",
  ].join("\n");
  const out = path.join(path.dirname(CONFIG_PATH), "posts", `${slug}.md`);
  console.log(`date:     ${date}`);
  if (dryRun) {
    console.log(`\ndry run -- would write ${path.relative(ROOT, out)}`);
    return;
  }
  const existed = fs.existsSync(out);
  fs.mkdirSync(path.dirname(out), { recursive: true });
  fs.writeFileSync(out, front + body);
  console.log(`\n${existed ? "updated" : "wrote"} ${path.relative(ROOT, out)}`);
  console.log(`url:      ${SITE}/blog/${slug}  (live once the file is committed and deployed)`);
}

function deriveSlug(file, title) {
  const season = (path.basename(file).match(/^(\d{4})-/) || [])[1];
  let s = title
    .replace(SERIES_PREFIX, "")
    .normalize("NFKD").replace(/[\u0300-\u036f]/g, "")
    .toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
  if (season && !s.startsWith(season)) s = `${season}-${s}`;
  return s;
}

async function main() {
  const file = process.argv[2];
  if (!file || file.startsWith("--")) {
    console.error("usage: node scripts/publish-article.mjs <file.md> --type T --author A [--featured] [--dry-run]");
    process.exit(1);
  }

  const md = fs.readFileSync(path.resolve(ROOT, file), "utf8");
  const { title, document } = markdownToRichText(md);

  const type = arg("--type");
  const author = arg("--author");
  const featured = process.argv.includes("--featured");
  const dryRun = process.argv.includes("--dry-run");

  if (!title) {
    console.error("no '# ' heading found -- the article needs one, it becomes the title field");
    process.exit(1);
  }
  if (!type || !author) {
    console.error("--type and --author are both required (author must be the Sleeper username)");
    process.exit(1);
  }

  const counts = {};
  for (const n of document.content) counts[n.nodeType] = (counts[n.nodeType] || 0) + 1;
  console.log(`title:    ${title}`);
  console.log(`type:     ${type}`);
  console.log(`author:   ${author}`);
  console.log(`featured: ${featured}`);
  const explicitSlug = arg("--slug");
  const derivedSlug = explicitSlug || deriveSlug(file, title);
  if (!/^[a-z0-9]+(-[a-z0-9]+)*$/.test(derivedSlug)) {
    console.error(`bad slug "${derivedSlug}" -- lowercase letters, digits and single hyphens only`);
    process.exit(1);
  }
  console.log(`slug:     ${derivedSlug}${explicitSlug ? "" : " (an existing post keeps its current slug)"}`);
  console.log(`blocks:   ${JSON.stringify(counts)}`);

  const backend = LEAGUE.blog?.backend || "markdown";
  if (backend === "markdown") return publishMarkdown({ md, title, type, author, featured, slug: derivedSlug, dryRun });
  if (backend !== "contentful") {
    console.error(`blog.backend is "${backend}" in league/league.json -- there is no blog to publish to`);
    process.exit(1);
  }

  if (dryRun) {
    fs.writeFileSync("/tmp/richtext-preview.json", JSON.stringify(document, null, 2));
    console.log("\ndry run -- wrote /tmp/richtext-preview.json, published nothing");
    return;
  }

  const env = loadEnv();
  const token = env.CONTENTFUL_MANAGEMENT_TOKEN;
  const space = env.CONTENTFUL_SPACE || env.VITE_CONTENTFUL_SPACE;
  if (!token) {
    console.error(
      "missing CONTENTFUL_MANAGEMENT_TOKEN in .env\n" +
        "  Create a Content management token in Contentful (Settings > API keys > Content\n" +
        "  management tokens) and put it in a local .env. Do NOT name it VITE_* and do NOT add\n" +
        "  it to Vercel -- nothing deployed writes to Contentful."
    );
    process.exit(1);
  }
  if (!space) {
    console.error("missing CONTENTFUL_SPACE (or VITE_CONTENTFUL_SPACE) in .env");
    process.exit(1);
  }

  const client = contentful.createClient({ accessToken: token });
  const environment = await (await client.getSpace(space)).getEnvironment("master");

  const fields = {
    title: { "en-US": title },
    body: { "en-US": document },
    type: { "en-US": type },
    author: { "en-US": author },
    featured: { "en-US": featured },
  };

  /*
  Match on title and update in place rather than always creating.

  Re-running after an edit is the normal case -- a typo, a rephrasing, a number that moved --
  and a create-only script turns each of those into a second copy of the same article on the
  live blog, which someone then has to find and unpublish by hand. Pass --new to force a
  separate entry when the title genuinely is being reused.
  */
  const existing = process.argv.includes("--new")
    ? { items: [] }
    : await environment.getEntries({ content_type: POST_TYPE, "fields.title": title });

  let entry;
  if (existing.items.length) {
    entry = existing.items[0];
    // `entry.fields = fields` replaces every field, so the slug has to be carried across
    // explicitly or each republish would erase it and break the post's URL.
    const keptSlug = explicitSlug || entry.fields.slug?.["en-US"] || derivedSlug;
    entry.fields = { ...fields, slug: { "en-US": keptSlug } };
    entry = await entry.update();
    await entry.publish();
    console.log(`\nupdated ${POST_TYPE} ${entry.sys.id}`);
    console.log(`url:      ${SITE}/blog/${keptSlug}`);
  } else {
    entry = await environment.createEntry(POST_TYPE, { fields: { ...fields, slug: { "en-US": derivedSlug } } });
    await entry.publish();
    console.log(`\npublished ${POST_TYPE} ${entry.sys.id}`);
    console.log(`url:      ${SITE}/blog/${derivedSlug}`);
  }
}

main().catch((e) => {
  console.error(e.message || e);
  process.exit(1);
});
