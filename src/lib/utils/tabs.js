import {leagueID} from '$lib/utils/leagueInfo';

/*
Nav structure. There is no Home tab: the seal above the nav links home, and dropping the tab is
what lets eight destinations fit the desktop bar. Managers leads because it is the page this
league actually uses -- it used to sit three levels deep in a dropdown.

Constraints this file has to respect, all of which live in NavLarge/NavSmall/Footer:

  * EXACTLY ONE tab may have `nest: true`. NavLarge picks the submenu contents with
    `for(const tab of tabs) if(tab.nest) tabChildren = tab.children` -- last one wins -- and
    renders a single shared submenu <div>. Add a second nested tab and hovering the first one
    silently shows the second one's children.
  * The Blog tab is hidden while `enableBlog` is false by testing `label == 'Blog'`, and
    NavSmall applies that test ONLY to non-nested tabs. So Blog must stay top-level and must
    keep exactly this label, or it starts showing again while the feature is off.
  * The Managers entry is hidden when the `managers` array is empty, also by label.

Group entries. Inside the nested tab's `children`, an entry of the form `{ group: 'History' }`
is a heading, not a destination: it has no `dest`, no `label` and no `icon`. NavLarge renders it
as a small caption, NavSmall as a list Subheader, and the Footer drops it with its
`.filter((link) => link.dest)`. Everything up to the next group entry belongs to that group.
Groups exist only inside the nested tab; a group entry at the top level would render as an
empty tab.

Off-site destinations are handled by testing the URL, not the label -- see navigate() and the
preload guards in NavLarge/NavSmall. Don't reintroduce a label test for external links; that is
what broke when the Keeper Draft Board was added alongside Go to Sleeper. The same `^https?://`
test adds the trailing open_in_new icon that marks a link as leaving the site.

Labels double as browser tab titles (src/lib/utils/pageTitle.js matches them on the path), so
renaming one renames the page's title too.
*/
export const tabs = [
    {
        icon: 'groups',
        label: 'Managers',
        dest: '/managers',
        key: 'managers',
    },
    {
        icon: 'sports',
        label: 'Matchups',
        dest: '/matchups',
        key: 'matchups',
    },
    {
        icon: 'leaderboard',
        label: 'Standings',
        dest: '/standings',
        key: 'standings',
    },
    {
        icon: 'person_search',
        label: 'Free Agents',
        dest: '/free-agents',
        key: 'free_agents',
    },
    {
        icon: 'swap_horiz',
        label: 'Trades & Waivers',
        dest: '/transactions',
        key: 'transactions',
    },
    {
        // Keep top-level, and keep this label -- see the note above.
        icon: 'article',
        label: 'Blog',
        dest: '/blog',
        key: 'blog',
    },
    {
        icon: 'view_comfy',
        label: 'League',
        nest: true,
        key: 'league',
        children: [
            { group: 'This Season' },
            {
                icon: 'storage',
                label: 'Rosters',
                dest: '/rosters',
            },
            { group: 'History' },
            {
                // /seasons/<year> lights this entry through findTab's first-segment fallback
                icon: 'calendar_month',
                label: 'Seasons',
                dest: '/seasons',
            },
            {
                icon: 'emoji_events',
                label: 'Trophy Room',
                dest: '/awards',
            },
            {
                icon: 'military_tech',
                label: 'Records',
                dest: '/records',
            },
            {
                icon: 'local_fire_department',
                label: 'Rivalry',
                dest: '/rivalry',
            },
            {
                icon: 'view_comfy',
                label: 'Drafts',
                dest: '/drafts',
            },
            { group: 'Rules & Tools' },
            {
                icon: 'history_edu',
                label: 'Constitution',
                dest: '/constitution',
            },
            {
                // companion project: separate repo, separate app, same league
                icon: 'calculate',
                label: 'Keeper Draft Board',
                dest: 'https://garrett-pdx.github.io/keeper-draft-board/',
            },
            {
                icon: 'lightbulb',
                label: 'Resources',
                dest: '/resources',
            },
            {
                icon: 'sports_football',
                label: 'Go to Sleeper',
                dest: `https://sleeper.app/leagues/${leagueID}`,
            },
        ]
    },
];

// Routes that belong to a tab without being its `dest`. The nav highlight and the tab title
// both treat a path listed here as if it were the tab it points at. /manager (one manager's
// page) lives under the Managers tab.
export const tabAliases = {
    '/manager': '/managers',
};

// The tab or dropdown child whose destination matches `pathname`, after aliasing; undefined
// for a page that isn't in the nav (the home page). A nested path with no tab of its own
// falls back to its first segment, so /blog/<slug> belongs to Blog.
// Returns [topLevelTab, child-or-undefined].
export const findTab = (pathname) => {
    const path = tabAliases[pathname] || pathname;
    const match = matchTab(path);
    if(match[0] || path.indexOf('/', 1) < 0) return match;
    return matchTab(path.slice(0, path.indexOf('/', 1)));
}

const matchTab = (path) => {
    for(const tab of tabs) {
        if(tab.dest == path) return [tab, undefined];
        if(tab.nest) {
            const child = tab.children.find(subTab => subTab.dest == path);
            if(child) return [tab, child];
        }
    }
    return [undefined, undefined];
}

// The `dest` of the nav entry that should be highlighted for `pathname`: the dropdown child if
// one matches, else the top-level tab. Undefined when nothing should be lit.
export const currentDest = (pathname) => {
    const [tab, child] = findTab(pathname);
    return (child || tab)?.dest;
}
