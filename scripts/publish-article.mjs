/**
 * Publish a Markdown article to Contentful as a blogPost entry.
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
 *   node scripts/publish-article.mjs <file.md> --type Preseason --author Gurret [--featured]
 *   node scripts/publish-article.mjs <file.md> ... --dry-run   # print the tree, publish nothing
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
  console.log(`blocks:   ${JSON.stringify(counts)}`);

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

  const entry = await environment.createEntry("blogPost", {
    fields: {
      title: { "en-US": title },
      body: { "en-US": document },
      type: { "en-US": type },
      author: { "en-US": author },
      featured: { "en-US": featured },
    },
  });
  await entry.publish();

  console.log(`\npublished blogPost ${entry.sys.id}`);
}

main().catch((e) => {
  console.error(e.message || e);
  process.exit(1);
});
