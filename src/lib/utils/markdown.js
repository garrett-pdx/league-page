/*
Markdown for the league's own prose: league/home.md, league/constitution.md and markdown blog
posts. Raw HTML passes through, so a league can still write markup where markdown falls short.
All of it is trusted content from the repo; never feed user input through here, because the
output is {@html}-injected.
*/
import { Marked } from 'marked';

const options = { gfm: true, breaks: false };
const marked = new Marked(options);

export const renderMarkdown = (src) => marked.parse(String(src || '').replace(/^﻿/, ''));
export const renderInline = (src) => marked.parseInline(String(src || ''));

/*
A constitution: every `## Heading` starts a numbered section and every `### Heading` inside it a
numbered rule, so the numbers never need renumbering by hand when a rule is added. Anything
before the first `##` is a preamble.

    [{ n: 1, id: 'section-1', title: 'The League',
       rules: [{ n: '1.1', id: 'rule-1-1', title: 'Format' }], html: '<h3 ...>1.1 Format</h3>...' }]

Titles come back as inline HTML. Rule headings are rendered with class "subSectionHeading" and
their id, so the table of contents can scroll to them.
*/
export const parseConstitution = (src) => {
    const tokens = marked.lexer(String(src || '').replace(/^﻿/, ''));
    let preamble = '';
    const sections = [];
    for(const t of tokens) {
        if(t.type === 'heading' && t.depth === 2) {
            sections.push({ n: sections.length + 1, title: renderInline(t.text), rules: [], raw: '' });
            continue;
        }
        const cur = sections[sections.length - 1];
        if(!cur) { preamble += t.raw; continue; }
        if(t.type === 'heading' && t.depth === 3) {
            const n = `${cur.n}.${cur.rules.length + 1}`;
            cur.rules.push({ n, id: `rule-${cur.n}-${cur.rules.length + 1}`, title: renderInline(t.text) });
        }
        cur.raw += t.raw;
    }

    return {
        preamble: preamble.trim() ? renderMarkdown(preamble) : '',
        sections: sections.map((s) => {
            let rule = 0;
            const sectionMarked = new Marked(options);
            sectionMarked.use({
                renderer: {
                    heading({ tokens, depth }) {
                        if(depth !== 3) return false;
                        const r = s.rules[rule++];
                        return `<h3 class="subSectionHeading" id="${r.id}">${r.n} ${this.parser.parseInline(tokens)}</h3>\n`;
                    },
                },
            });
            return { n: s.n, id: `section-${s.n}`, title: s.title, rules: s.rules, html: sectionMarked.parse(s.raw) };
        }),
    };
};
