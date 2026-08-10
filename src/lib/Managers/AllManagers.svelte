<script>
    import { leagueName } from '$lib/utils/helper';
    import { getDatesActive } from '$lib/utils/helperFunctions/universalFunctions';
    import ManagerRow from './ManagerRow.svelte'

    export let managers, leagueTeamManagers;

    let innerWidth;

    /*
    Managers who have left the league are split out into the Moratorium below the
    active roster. They're detected from Sleeper -- getDatesActive only fills in
    `end` once a manager stops appearing on a roster -- rather than from a flag in
    leagueInfo, so a manager who leaves needs no code change beyond staying in the
    array. `key` deliberately stays the index into the ORIGINAL array: it drives
    /manager?manager=N and rival.link, both of which are positional.
    */
    const indexed = managers.map((manager, key) => ({manager, key}));
    const departedYear = (manager) => manager.managerID
        ? (getDatesActive(leagueTeamManagers, manager.managerID) || {}).end
        : null;
    $: active = indexed.filter(({manager}) => !departedYear(manager));
    $: departed = indexed.filter(({manager}) => departedYear(manager));
</script>

<svelte:window bind:innerWidth={innerWidth} />

<style>
    .managerContainer {
        width: 100%;
        margin: 2em 0 5em;
    }

    .managerConstrained {
        width: 97%;
        max-width: 800px;
        margin: 0 auto;
    }

    h2 {
        text-align: center;
        font-size: 2.8em;
        margin: 2em 0 1.5em;
        line-height: 1em;
    }

    .moratorium {
        margin-top: 4em;
        border-top: 1px solid var(--ccc);
        padding-top: 1em;
    }

    .moratoriumHeading {
        font-size: 1.9em;
        margin: 1.2em 0 0.2em;
    }

    .moratoriumBlurb {
        text-align: center;
        color: var(--g555);
        font-style: italic;
        margin: 0 auto 2em;
        max-width: 34em;
        line-height: 1.4em;
    }

    @media (max-width: 520px) {
        h2 {
            text-align: center;
            font-size: 2em;
            margin: 1.5em 0 1em;
            line-height: 1em;
        }

        .moratoriumHeading {
            font-size: 1.5em;
        }
    }
</style>

<div class="managerContainer">
    <h2>{leagueName} Managers</h2>
    <div class="managerConstrained">
        {#each active as {manager, key} (key)}
            <ManagerRow {manager} {leagueTeamManagers} {key} />
        {/each}
    </div>

    {#if departed.length}
        <div class="moratorium">
            <h2 class="moratoriumHeading">Moratorium</h2>
            <p class="moratoriumBlurb">
                Managers who are no longer with us. Their results still count in the
                all-time records, which is its own kind of afterlife.
            </p>
            <div class="managerConstrained">
                {#each departed as {manager, key} (key)}
                    <ManagerRow {manager} {leagueTeamManagers} {key} />
                {/each}
            </div>
        </div>
    {/if}
</div>
