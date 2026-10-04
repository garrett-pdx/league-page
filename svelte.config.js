import vercel from '@sveltejs/adapter-vercel';
import node from '@sveltejs/adapter-node';

const dockerBuild = process.env.DOCKER_BUILD

/** @type {import('@sveltejs/kit').Config} */
const config = {
	kit: {
		adapter: dockerBuild ? node() : vercel(),
		// league/ holds everything about one league (see league/README.md); the engine imports
		// it as $league so no component ever reaches for a relative path out of src/.
		// LEAGUE_DIR points it at another league's directory, to preview that league
		// (see `npm run dev:league` and scripts/try-league.sh).
		alias: {
			$league: process.env.LEAGUE_DIR || 'league',
		},
	}
};

export default config;
