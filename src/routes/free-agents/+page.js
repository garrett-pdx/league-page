import { getNflState, loadPlayers, waitForAll } from '$lib/utils/helper';

export async function load({fetch}) {
    const freeAgents = fetch('/api/fetch_free_agents')
        .then(res => {
            if(!res.ok) throw new Error('Could not load free agents');
            return res.json();
        });

    // projections come from the shared players cache; the page still works without them
    const extras = waitForAll(
        loadPlayers(fetch).catch(() => ({players: {}})),
        getNflState().catch(() => ({})),
    );

    return {
        freeAgents,
        extras,
    };
}
