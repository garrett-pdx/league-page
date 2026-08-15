import {leagueID} from '$lib/utils/leagueInfo';

/*
Nav structure. Managers and Standings are top-level on purpose -- Managers especially, since it
is the page this league actually uses and it used to sit three levels deep in a dropdown.

Three constraints this file has to respect, all of which live in NavLarge/NavSmall/Footer:

  * EXACTLY ONE tab may have `nest: true`. NavLarge picks the submenu contents with
    `for(const tab of tabs) if(tab.nest) tabChildren = tab.children` -- last one wins -- and
    renders a single shared submenu <div>. Add a second nested tab and hovering the first one
    silently shows the second one's children.
  * The Blog tab is hidden while `enableBlog` is false by testing `label == 'Blog'`, and
    NavSmall applies that test ONLY to non-nested tabs. So Blog must stay top-level and must
    keep exactly this label, or it starts showing again while the feature is off.
  * The Managers entry is hidden when the `managers` array is empty, also by label.

Off-site destinations are handled by testing the URL, not the label -- see navigate() and the
preload guards in NavLarge/NavSmall. Don't reintroduce a label test for external links; that is
what broke when the Keeper Draft Board was added alongside Go to Sleeper.
*/
export const tabs = [
    {
        icon: 'home',
        label: 'Home',
        dest: '/',
        key: 'home',
    },
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
        label: 'League Info',
        nest: true,
        key: 'league_info',
        children: [
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
                icon: 'view_comfy',
                label: 'Drafts',
                dest: '/drafts',
            },
            {
                icon: 'local_fire_department',
                label: 'Rivalry',
                dest: '/rivalry',
            },
            {
                icon: 'storage',
                label: 'Rosters',
                dest: '/rosters',
            },
            {
                icon: 'history_edu',
                label: 'Constitution',
                dest: '/constitution',
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
            {
                // companion project: separate repo, separate app, same league
                icon: 'calculate',
                label: 'Keeper Draft Board',
                dest: 'https://garrett-pdx.github.io/keeper-draft-board/',
            },
        ]
    },
];
