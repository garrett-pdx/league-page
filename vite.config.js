import { sveltekit } from '@sveltejs/kit/vite';

/** @type {import('vite').UserConfig} */
const config = {
	plugins: [sveltekit()],
	server: {
		fs: {
			// SvelteKit narrows the dev server's file allowlist to src/, node_modules and a few
			// others. league/ (the league's config, prose and photos) has to be on it too, or
			// the dev server answers 403 for league.json.
			allow: ['league'],
		},
	},
};

export default config;
