/*
The PWA manifest, built from league.json so the installed app carries the league's name.
Prerendered: it is a static file in the build, served at /manifest.json as before.
*/
import { json } from '@sveltejs/kit';
import { leagueName, leagueShortName, leagueDescription } from '$lib/utils/leagueInfo';

export const prerender = true;

export const GET = () => json({
    short_name: leagueShortName,
    name: leagueName,
    icons: [
        {
            "src": "/favicons/android-chrome-192x192.png",
            "sizes": "192x192",
            "type": "image/png",
            "purpose": "maskable any"
        },
        {
            "src": "/favicons/android-chrome-512x512.png",
            "sizes": "512x512",
            "type": "image/png",
            "purpose": "maskable any"
        }
    ],
    start_url: '/',
    background_color: '#fff',
    display: 'standalone',
    scope: '/',
    theme_color: '#fff',
    shortcuts: [
        {
            "name": "Trades and Waivers",
            "short_name": "Transactions",
            "description": "View league trades and waivers",
            "url": "/transactions"
        },
        {
            "name": "Matchups",
            "short_name": "Matchups",
            "description": "View league matchups",
            "url": "/matchups"
        },
        {
            "name": "Rosters",
            "short_name": "Rosters",
            "description": "View league rosters",
            "url": "/rosters"
        },
        {
            "name": "Drafts",
            "short_name": "Drafts",
            "description": "View league upcoming and past drafts",
            "url": "/drafts"
        },
        {
            "name": "Trophy Room",
            "short_name": "Trophy Room",
            "description": "View the managers' past awards and accomplishments",
            "url": "/awards"
        },
        {
            "name": "Resources & News",
            "short_name": "Resources",
            "description": "View fantasy football resources and news",
            "url": "/resources"
        }
    ],
    description: leagueDescription || `Standings, matchups, records and history for ${leagueName}`,
});
