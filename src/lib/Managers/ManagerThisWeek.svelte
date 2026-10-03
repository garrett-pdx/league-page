<script>
    import { onMount } from 'svelte';
    import { getNflState, getLeagueMatchups } from '$lib/utils/helper';
    import { getRosterIDFromManagerIDAndYear, getTeamNameFromTeamManagers } from '$lib/utils/helperFunctions/universalFunctions';

    /*
    "This week: vs {opponent}" under a manager's location line, linking to /matchups. Mounted in
    Manager.svelte.

    Hidden unless there is something true to say: outside the regular season, for a manager with
    no roster this season (the Moratorium), or when the week has no pairing for them. The NFL
    state is checked FIRST, so an offseason visit never triggers getLeagueMatchups(), which fetches
    every regular-season week. It is memoized, so in season it costs nothing the Matchups page
    would not.
    */
    export let managerID, leagueTeamManagers;

    let opponent = null;

    onMount(async () => {
        try {
            const state = await getNflState();
            if(state.season_type != 'regular') return;

            const matchups = await getLeagueMatchups();
            const rosterID = getRosterIDFromManagerIDAndYear(leagueTeamManagers, managerID, matchups.year);
            if(!rosterID) return;

            const weekData = matchups.matchupWeeks.find((w) => w.week == matchups.week);
            if(!weekData) return;

            for(const pairing of Object.values(weekData.matchups)) {
                if(pairing.length != 2) continue;
                const mine = pairing.findIndex((t) => t.roster_id == rosterID);
                if(mine < 0) continue;
                const them = pairing[1 - mine].roster_id;
                opponent = getTeamNameFromTeamManagers(leagueTeamManagers, them, matchups.year);
                return;
            }
        } catch(err) {
            // a convenience line: never let it take the manager page down
            console.error(err);
        }
    });
</script>

<style>
    .thisWeek {
        text-align: center;
        margin: -0.8em 0 1.4em;
    }

    a {
        display: inline-flex;
        align-items: center;
        min-height: 44px;
        padding: 0 0.8em;
        font-size: 0.9375rem;
        color: var(--accentInk);
        text-decoration: none;
    }

    a:hover {
        text-decoration: underline;
    }

    a:focus-visible {
        outline: 2px solid var(--blueOne);
        outline-offset: 2px;
    }

    strong {
        font-weight: 500;
        margin-left: 0.3em;
    }
</style>

{#if opponent}
    <p class="thisWeek">
        <a href="/matchups">This week: vs <strong>{opponent}</strong></a>
    </p>
{/if}
