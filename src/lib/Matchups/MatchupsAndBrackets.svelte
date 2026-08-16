
<script>
	import LinearProgress from '@smui/linear-progress';
	import MatchupWeeks from './MatchupWeeks.svelte';
	import Brackets from './Brackets.svelte';
    import Button, { Group, Label } from '@smui/button';
    import { goto } from '$app/navigation';
    import { onMount } from 'svelte';
    import { loadPlayers, getUpcomingDraft } from '$lib/utils/helper';
    import { SectionHeading, Countdown } from '$lib/Design';

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

    onMount(async () => {
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
        margin: 3em 0;
    }
</style>



{#if loading}
    <!-- promise is pending -->
    <div class="message">
        <p>Loading league matchups...</p>
        <LinearProgress indeterminate />
    </div>
{:else}
    {#if matchupWeeks.length}
        <div class="buttonHolder">
            <Group variant="outlined">
                <!-- Regular Season -->
                <Button class="selectionButtons" onclick={() => changeSelection('regular')} variant="{selection == 'regular' ? "raised" : "outlined"}">
                    <Label>Regular Season</Label>
                </Button>
                <!-- Championship Bracket -->
                <Button class="selectionButtons" onclick={() => changeSelection('champions')} variant="{selection == 'champions' || selection == 'losers' ? "raised" : "outlined"}">
                    <Label>Playoffs</Label>
                </Button>
            </Group>
            {#if selection == 'champions' || selection == 'losers'}
                <Group variant="outlined">
                    <!-- Championship Bracket -->
                    <Button class="selectionButtons" onclick={() => changeSelection('champions')} variant="{selection == 'champions' ? "raised" : "outlined"}">
                        <Label>Champions' Bracket</Label>
                    </Button>
                    <!-- Losers Bracket -->
                    <Button class="selectionButtons" onclick={() => changeSelection('losers')} variant="{selection == 'losers' ? "raised" : "outlined"}">
                        <Label>Losers' Bracket</Label>
                    </Button>
                </Group>
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