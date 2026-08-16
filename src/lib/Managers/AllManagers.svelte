<script>
    import { leagueName } from '$lib/utils/helper';
    import { getDatesActive } from '$lib/utils/helperFunctions/universalFunctions';
    import { SectionHeading, SegmentedControl } from '$lib/Design';
    import ManagerRow from './ManagerRow.svelte'

    let { managers, leagueTeamManagers } = $props();

    /*
    Managers who have left the league are split out into the Moratorium. They're detected
    from Sleeper -- getDatesActive only fills in `end` once a manager stops appearing on a
    roster -- rather than from a flag in leagueInfo, so a manager who leaves needs no code
    change beyond staying in the array. `key` deliberately stays the index into the ORIGINAL
    array: it drives /manager?manager=N and rival.link, both of which are positional.
    */
    const indexed = managers.map((manager, key) => ({manager, key}));
    const departedYear = (manager) => manager.managerID
        ? (getDatesActive(leagueTeamManagers, manager.managerID) || {}).end
        : null;

    const active = indexed.filter(({manager}) => !departedYear(manager));
    const departed = indexed.filter(({manager}) => departedYear(manager));

    let view = $state('active');
    const shown = $derived(view === 'active' ? active : departed);

    const options = [
        {value: 'active', label: `Active (${active.length})`},
        {value: 'moratorium', label: `Moratorium (${departed.length})`},
    ];
</script>

<style>
    .managerContainer {
        width: 100%;
        margin: 0 0 5em;
    }

    .controls {
        display: flex;
        justify-content: center;
        margin: 0 auto 1.6em;
    }

    .grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 1.1em;
        width: 94%;
        max-width: var(--pageMax);
        margin: 0 auto;
    }

    .blurb {
        text-align: center;
        color: var(--g555);
        font-style: italic;
        margin: 0 auto 2em;
        max-width: 34em;
        line-height: 1.4em;
        width: 90%;
    }

    @media (max-width: 640px) {
        .grid {
            grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
            gap: 0.8em;
        }
    }
</style>

<div class="managerContainer">
    <SectionHeading eyebrow={leagueName} level={2}>Managers</SectionHeading>

    {#if departed.length}
        <div class="controls">
            <SegmentedControl {options} bind:value={view} ariaLabel="Show active managers or the Moratorium" />
        </div>
    {/if}

    {#if view === 'moratorium'}
        <p class="blurb">
            Managers who are no longer with us. Their results still count in the
            all-time records, which is its own kind of afterlife.
        </p>
    {/if}

    <div class="grid">
        {#each shown as {manager, key} (key)}
            <ManagerRow {manager} {leagueTeamManagers} {key} />
        {/each}
    </div>
</div>
