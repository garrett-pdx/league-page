
<script>
	import LinearProgress from '@smui/linear-progress';
	import MatchupWeeks from './MatchupWeeks.svelte';
	import Brackets from './Brackets.svelte';
    import { goto } from '$app/navigation';
    import { onMount } from 'svelte';
    import { loadPlayers, getUpcomingDraft } from '$lib/utils/helper';
    import { SectionHeading, Countdown, SegmentedControl } from '$lib/Design';

    /*
    Preseason only. This page previously rendered the single line "No upcoming matchups..." with
    no page heading at all -- on a top-level nav item, from February to September.

    startTime is null once the draft completes, so the countdown disappears on its own rather
    than counting toward a date in the past. See the note in helperFunctions/leagueDrafts.js.
    */
    const draftData = getUpcomingDraft();

	export let queryWeek, leagueTeamManagersData, matchupsData, bracketsData, playersData;

    let players, matchupWeeks, year, week, regularSeasonLength, brackets, leagueTeamManagers;

    let loading = true;
    let loadError = false;

    onMount(async () => {
        /*
        Every other route resolves its promises through {#await}{:then}{:catch} at the route
        level (see src/routes/CLAUDE.md). This component instead awaits four promises in a bare
        onMount, which means a rejection from any of them -- a Sleeper timeout, a 500, an
        ordinary network blip, all real possibilities against an unauthenticated third-party API
        with no retry -- throws with nothing to catch it. loading never flips to false, so
        matchups is a top-level nav item that gets stuck on "Loading league matchups..." forever,
        with only a console error to show for it. Same shape as the fix in Standings/index.svelte.
        */
        try {
            brackets = await bracketsData;
            const matchupsInfo = await matchupsData;
            leagueTeamManagers = await leagueTeamManagersData;
            matchupWeeks = matchupsInfo.matchupWeeks;
            year = matchupsInfo.year;
            week = matchupsInfo.week;
            regularSeasonLength = matchupsInfo.regularSeasonLength;
            const playersInfo = await playersData;
            players = playersInfo.players;
            loading = false;

            if(playersInfo.stale) {
                const newPlayersInfo = await loadPlayers(null, true);
                players = newPlayersInfo.players;
            }
        } catch(err) {
            console.error(err);
            loadError = true;
            loading = false;
        }
    });

    const changeSelection = (s) => {
        if(s == 'regular') {
            queryWeek = 1;
            goto(`/matchups?week=1`, {noscroll: true});
        } else if(selection == 'regular') {
            queryWeek = 99;
            goto(`/matchups?week=99`, {noscroll: true});
        }
        selection = s;
    }

    let selection = 'regular';

    const modeOptions = [
        { value: 'regular', label: 'Regular Season' },
        { value: 'champions', label: 'Playoffs' },
    ];
    const bracketOptions = [
        { value: 'champions', label: "Champions' Bracket" },
        { value: 'losers', label: "Losers' Bracket" },
    ];
</script>

<style>
    .message {
        display: block;
        width: 92%;
        max-width: 560px;
        margin: 2em auto 6em;
        text-align: center;
        color: var(--g555);
    }

    .untilDraft {
        margin-top: 2.5em;
        padding: 1.4em 1em;
        background-color: var(--fff);
        border-radius: var(--radiusMd);
        box-shadow: var(--shadowCard);
    }

    .buttonHolder {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.75em;
        margin: 3em 0;
        padding: 0 12px;
    }
</style>



{#if loading}
    <!-- promise is pending -->
    <div class="message">
        <p>Loading league matchups...</p>
        <LinearProgress indeterminate />
    </div>
{:else if loadError}
    <div class="message">
        <p>Something went wrong loading matchups. Try refreshing the page.</p>
    </div>
{:else}
    {#if matchupWeeks.length}
        <div class="buttonHolder">
            <SegmentedControl options={modeOptions} value={selection == 'regular' ? 'regular' : 'champions'} onchange={changeSelection} ariaLabel="Regular season or playoffs" />
            {#if selection == 'champions' || selection == 'losers'}
                <SegmentedControl options={bracketOptions} value={selection} onchange={changeSelection} ariaLabel="Champions' or losers' bracket" />
            {/if}
        </div>
        {#if selection == 'regular'}
            <MatchupWeeks {players} {queryWeek} {matchupWeeks} {regularSeasonLength} {year} {week} bind:selection={selection} {leagueTeamManagers} />
        {/if}
    {:else}
        <div class="message">
            <SectionHeading eyebrow="Preseason" accent="gold">No Matchups Yet</SectionHeading>
            <p>The schedule appears once the season kicks off in week one. Until then, the
            draft is the only thing on the calendar.</p>

            {#await draftData then draft}
                {#if draft?.startTime}
                    <div class="untilDraft">
                        <Countdown
                            target={draft.startTime}
                            label="{draft.year} Draft"
                            expiredLabel="Drafting now"
                        />
                    </div>
                {/if}
            {:catch}
                <!-- decoration; a failed draft fetch must not take the page down -->
            {/await}
        </div>
    {/if}
    <!-- {promise has processed -->
    {#if brackets.champs.bracket[0][0][0].points && (selection == 'champions' || selection == 'losers')}
        <Brackets {queryWeek} {leagueTeamManagers} {players} {brackets} bind:selection={selection} />
    {/if}
{/if}