/*
The markdown blog backend: league/posts/*.md, one file per post, published by committing it.

    ---
    title: Week 4 preview
    date: 2026-09-30
    type: Preview
    author: commish
    featured: true
    ---
    The post, in markdown. Tables, lists, links and raw HTML all work.

  title     required, unless the body opens with a `# Heading`, which is then the title
  date      YYYY-MM-DD (or a full ISO time); orders the posts, newest first
  type      the post's category; the /blog filter is built from the posts' own types
  author    the author's Sleeper username, which links the byline to their manager page
  featured  true puts the post on the home page (else the newest post is shown there)
  slug      the URL, /blog/<slug>; defaults to the file name without .md
  draft     true keeps the post off the site

Each post comes back in the shape the Contentful backend returns -- {sys: {id, createdAt},
fields: {title, slug, type, author, featured, body}} -- so the blog components serve both. The
body is a document with one `html` node (see generateParagraph in getBlogPosts.js), rendered with
the same CSS classes the Contentful renderer emits, so posts look the same whichever backend
serves them. Pure functions, no $lib imports; the API route does the file loading.
*/
import { Marked } from 'marked';

const blogMarked = new Marked({ gfm: true, breaks: false });
blogMarked.use({
    renderer: {
        heading({ tokens, depth }) {
            return `<h${depth} class="heading-${depth}">${this.parser.parseInline(tokens)}</h${depth}>\n`;
        },
        paragraph({ tokens }) {
            return `<p class="bodyParagraph">${this.parser.parseInline(tokens)}</p>\n`;
        },
    },
});

/** Split `---` frontmatter of `key: value` lines from the body. Values are strings or booleans. */
export const parseFrontmatter = (src) => {
    const text = String(src || '').replace(/^﻿/, '');
    const m = text.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?/);
    if(!m) return { meta: {}, body: text };
    const meta = {};
    for(const line of m[1].split(/\r?\n/)) {
        const kv = line.match(/^\s*([A-Za-z][\w-]*)\s*:\s*(.*?)\s*$/);
        if(!kv) continue;
        let value = kv[2].replace(/^(["'])(.*)\1$/, '$2');
        if(value === 'true') value = true;
        else if(value === 'false') value = false;
        meta[kv[1]] = value;
    }
    return { meta, body: text.slice(m[0].length) };
};

const isoDate = (value) => {
    if(!value) return null;
    // A bare date is pinned to noon UTC, so it shows as that date in every timezone.
    const iso = /^\d{4}-\d{2}-\d{2}$/.test(value) ? `${value}T12:00:00Z` : value;
    const t = Date.parse(iso);
    return Number.isNaN(t) ? null : new Date(t).toISOString();
};

/**
 * One post from a file name and its source, or null for a draft or a file with no title.
 * Problems come back in `error` rather than throwing, so one bad file cannot take the blog down.
 */
export const postFromMarkdown = (fileName, src) => {
    const { meta, body } = parseFrontmatter(src);
    if(meta.draft === true) return null;
    let markdown = body;
    let title = meta.title;
    if(!title) {
        const h1 = markdown.match(/^\s*#\s+(.+?)\s*#*\s*$/m);
        if(h1 && markdown.trimStart().startsWith('#')) {
            title = h1[1];
            markdown = markdown.replace(h1[0], '');
        }
    }
    const slug = meta.slug || fileName.replace(/^.*\//, '').replace(/\.md$/, '');
    if(!title) return { error: `${fileName}: no title (add "title:" to the frontmatter)` };
    const createdAt = isoDate(meta.date);
    if(!createdAt) return { error: `${fileName}: missing or unreadable "date:" (use YYYY-MM-DD)` };
    return {
        sys: { id: slug, createdAt },
        fields: {
            title,
            slug,
            type: meta.type || 'Post',
            author: meta.author || '',
            featured: meta.featured === true,
            body: { nodeType: 'document', content: [{ nodeType: 'html', html: blogMarked.parse(markdown) }] },
        },
    };
};

/** Every published post from {fileName: source}, newest first, plus any file problems. */
export const postsFromFiles = (files) => {
    const items = [];
    const errors = [];
    for(const [name, src] of Object.entries(files)) {
        const post = postFromMarkdown(name, src);
        if(!post) continue;
        if(post.error) errors.push(post.error);
        else items.push(post);
    }
    items.sort((a, b) => Date.parse(b.sys.createdAt) - Date.parse(a.sys.createdAt));
    return { items, errors };
};
