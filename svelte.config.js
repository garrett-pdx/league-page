import vercel from '@sveltejs/adapter-vercel';
import node from '@sveltejs/adapter-node';

const dockerBuild = process.env.DOCKER_BUILD

/** @type {import('@sveltejs/kit').Config} */
const config = {
	kit: {
		adapter: dockerBuild ? node() : vercel(),
		// league/ holds everything about one league (see league/README.md); the engine imports
		// it as $league so no component ever reaches for a relative path out of src/.
		alias: {
			$league: 'league',
		},
	}
};

export default config;
