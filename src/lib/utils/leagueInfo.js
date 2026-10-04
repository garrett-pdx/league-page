/*
The league's configuration, as the rest of the site sees it.

Nothing league-specific is written here. Everything comes from league/ -- league.json (validated
against schema/league.schema.json), home.md and the photos in league/managers/ -- and this file
turns it into the exports the components have always imported: leagueID, leagueName, managers,
homepageText and the blog flags. To change what the site says about a league, edit league/, not
this file.
*/
import config from '$league/league.json';
import { renderMarkdown, parseConstitution } from './markdown';

// Optional prose files. A glob rather than an import, so a league without one still builds.
const prose = import.meta.glob(['/league/home.md', '/league/constitution.md'], { eager: true, query: '?raw', import: 'default' });

export const league = config;

export const leagueID = config.sleeperLeagueId;
export const leagueName = config.name;
export const leagueShortName = config.shortName || config.name;
export const leagueDescription = config.description || '';
export const siteUrl = config.siteUrl || '';
export const founded = config.founded ?? null;
export const dynasty = Boolean(config.dynasty);

const blog = config.blog || {};
export const blogBackend = blog.backend || 'markdown';
export const enableBlog = blogBackend !== 'none';
export const blogTitle = blog.title || 'Blog';
export const blogIntro = blog.intro || '';

/*
Comments write to Contentful, which takes a *management* token -- full write access to the
space. Vite exposes anything prefixed VITE_ to the browser, so that token must never be set as
VITE_CONTENTFUL_ACCESS_TOKEN on a public site. Turning comments on means setting the token AND
moving it off import.meta.env onto SvelteKit's $env/static/private in
src/routes/api/addBlogComments/[id]/+server.js, so it stays server-side. Do not just flip
blog.comments.
*/
export const enableComments = blogBackend === 'contentful' && Boolean(blog.comments);

// Contentful derives a content type's ID from its display name ("Blog Post" -> blogPost), so
// the IDs are configuration, not constants.
export const contentfulTypes = {
    post: blog.contentful?.postType || 'blog_post',
    comment: blog.contentful?.commentType || 'blog_comment',
};

/*
The one-line intro under each page's title. These are the league's voice, so league.json can
replace any of them (pages.<key>.intro); the defaults hold no league-specific facts.
*/
const DEFAULT_INTROS = {
    managers: 'Every manager and one group chat. Pick a name for the bio, the roster and the record.',
    standings: 'Wins first, then points scored. The table does not take requests.',
    'free-agents': "Every unrostered player, by depth-chart slot. Handcuff hunters: start with the RB2s. Turn on Show rostered to see who's already taken.",
    transactions: 'Every trade and waiver claim on record, newest first. Receipts, for anyone who remembers it differently.',
    rosters: 'Every roster, as it stands right now. Scouting is allowed.',
    seasons: 'Every season on record, one page each. The results are final; the arguments are not.',
    awards: 'Champions, podiums and toilet bowl losers, kept permanently.',
    records: 'Highs, lows and close calls from every season on record. The lows are included on purpose.',
    rivalry: 'Pick any two managers. The history is already in the books.',
    drafts: 'Every draft on record. None of it can be undone.',
    'stat-lab': 'Every game on record. Filter it, sort it, chart it, and send the link to the group chat.',
    resources: "The league's own links first, then rankings, news and a few podcasts. Outside advice, taken at your own risk.",
};
export const pageIntro = (key) => config.pages?.[key]?.intro ?? DEFAULT_INTROS[key] ?? null;

export const homepageText = renderMarkdown(prose['/league/home.md'] || '');

// The constitution, parsed into numbered sections and rules (null when the league has none).
export const constitution = prose['/league/constitution.md'] ? parseConstitution(prose['/league/constitution.md']) : null;

/*
Links. `{sleeper}` in a URL stands for the league's page on Sleeper. A link to an internal page
whose feature is off (the blog) is dropped rather than left pointing at nothing.
*/
const sleeperUrl = `https://sleeper.app/leagues/${leagueID}`;
const resolveLink = (link) => ({ ...link, url: link.url.replace('{sleeper}', sleeperUrl) });
const linkEnabled = (link) => enableBlog || !/^\/blog(\/|$)/.test(link.url);
export const leagueLinks = (config.links?.league || []).map(resolveLink).filter(linkEnabled);
export const elsewhereLinks = (config.links?.elsewhere || []).map(resolveLink).filter(linkEnabled);
export const navLinks = leagueLinks
    .filter((link) => link.nav)
    .map((link) => ({ label: link.nav.label || link.name, icon: link.nav.icon || link.icon, dest: link.url }));

// Seasons played before the league came to Sleeper, oldest first.
export const preSleeperSeasons = [...(config.history?.preSleeper || [])].sort((a, b) => a.season - b.season);
export const preSleeperSeason = (year) => preSleeperSeasons.find((s) => s.season === Number(year)) || null;

/*
Photos. A file name resolves to league/managers/<file>, bundled by Vite (so it is fingerprinted
and cached forever); a full URL is used as is; everyone.png and question.jpg are built-in
placeholders served from static/managers/.
*/
const photoFiles = import.meta.glob('/league/managers/*.{jpg,jpeg,png,webp,gif,avif,svg}', {
    eager: true,
    query: '?url',
    import: 'default',
});
const BUILT_IN_PHOTOS = ['everyone.png', 'question.jpg'];
export const photoUrl = (photo) => {
    if(!photo) return '/managers/question.jpg';
    if(/^(https?:)?\/\//.test(photo) || photo.startsWith('/')) return photo;
    const bundled = photoFiles[`/league/managers/${photo}`];
    if(bundled) return bundled;
    if(BUILT_IN_PHOTOS.includes(photo)) return `/managers/${photo}`;
    console.warn(`league.json: no photo "${photo}" in league/managers/`);
    return '/managers/question.jpg';
};

/*
Managers, in the shape the components were written against: `managerID`, a resolved `photo`,
and `rival: { name, link, image }`, where `link` is an index into this array (or null for the
all-managers page). league.json names a rival by userId instead, so reordering managers there
can never quietly re-pair them; the index is computed here.
*/
const entries = config.managers || [];
const indexOf = Object.fromEntries(entries.map((m, i) => [m.userId, i]));

const rivalOf = (m) => {
    const r = m.rival;
    if(r?.userId && indexOf[r.userId] !== undefined) {
        const other = entries[indexOf[r.userId]];
        return { name: other.name, link: indexOf[r.userId], image: photoUrl(other.photo) };
    }
    if(r?.name) return { name: r.name, link: null, image: photoUrl(r.photo || 'everyone.png') };
    return { name: 'The Field', link: null, image: photoUrl('everyone.png') };
};

export const managers = entries.map((m) => {
    const { userId, photo, rival, ...rest } = m;
    return { managerID: userId, ...rest, photo: photoUrl(photo), rival: rivalOf(m) };
});
