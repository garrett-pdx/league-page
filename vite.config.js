import { sveltekit } from '@sveltejs/kit/vite';
import fs from 'node:fs';
import path from 'node:path';

/*
Previewing another league: LEAGUE_DIR (its league.json, prose and photos) and LEAGUE_DATA (its
static/data) point the dev server somewhere other than league/ and static/data/. scripts/
try-league.sh writes both for any Sleeper league ID; `npm run dev:league -- <dir>` serves one.
*/
const leagueDir = process.env.LEAGUE_DIR ? path.resolve(process.env.LEAGUE_DIR) : null;
const leagueData = process.env.LEAGUE_DATA ? path.resolve(process.env.LEAGUE_DATA) : null;

// In dev, answer /data/<file> from LEAGUE_DATA instead of static/data.
const serveLeagueData = () => ({
	name: 'serve-league-data',
	configureServer(server) {
		// A previewed league's directory is usually outside the project, which Vite does not
		// watch; without this, a new post or photo there needs a server restart.
		if(leagueDir) server.watcher.add(leagueDir);
		if(!leagueData) return;
		server.middlewares.use('/data', (req, res, next) => {
			const file = path.join(leagueData, decodeURIComponent(req.url.split('?')[0]));
			if(!file.startsWith(leagueData) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) return next();
			res.setHeader('Content-Type', file.endsWith('.json') ? 'application/json' : 'application/octet-stream');
			fs.createReadStream(file).pipe(res);
		});
	},
});

/** @type {import('vite').UserConfig} */
const config = {
	plugins: [serveLeagueData(), sveltekit()],
	// A preview runs beside the normal dev server; sharing Vite's dependency cache would load
	// two copies of the Svelte runtime into whichever server optimised second.
	...(leagueDir ? { cacheDir: 'node_modules/.vite-league' } : {}),
	server: {
		fs: {
			// SvelteKit narrows the dev server's file allowlist to src/, node_modules and a few
			// others. league/ (the league's config, prose and photos) has to be on it too, or
			// the dev server answers 403 for league.json.
			allow: ['league', ...[leagueDir, leagueData].filter(Boolean)],
		},
	},
};

export default config;
