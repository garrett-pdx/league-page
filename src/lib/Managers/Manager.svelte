<script>
    import Button, { Group, Label } from '@smui/button';
	import LinearProgress from '@smui/linear-progress';
    import {loadPlayers, getLeagueTransactions, getManagerCareer, ordinal} from '$lib/utils/helper';
	import { StatTile } from '$lib/Design';
	import Roster from '../Rosters/Roster.svelte';
	import TransactionsPage from '../Transactions/TransactionsPage.svelte';
    import { goto } from '$app/navigation';
    import ManagerFantasyInfo from './ManagerFantasyInfo.svelte';
    import ManagerAwards from './ManagerAwards.svelte';
    import { onMount } from 'svelte';
	import { getDatesActive, getRosterIDFromManagerID, getDistinctTeamName } from '$lib/utils/helperFunctions/universalFunctions';

    export let manager, managers, rostersData, leagueTeamManagers, rosterPositions, transactionsData, awards, records, leagueHistory = null;

    let transactions = transactionsData.transactions;

    $: viewManager = managers[manager];

    $: datesActive = getDatesActive(leagueTeamManagers, viewManager.managerID);

    const  startersAndReserve = rostersData.startersAndReserve;
    let rosters = rostersData.rosters;

    $: ({rosterID, year} = viewManager.managerID ? getRosterIDFromManagerID(leagueTeamManagers, viewManager.managerID) : {rosterID: viewManager.roster, year: null});

    $: teamName = getDistinctTeamName(leagueTeamManagers, rosterID, year, viewManager.name);

    /*
    A departed manager's rosterID belongs to his LAST season, but `rosters` and
    `transactions` are the CURRENT season's. Indexing them by that old id silently
    shows whoever holds that roster slot today -- Jordan Leonard's page was rendering
    Brenden Brown's roster and transactions. Gate both on the manager still being active.
    */
    $: isFormerManager = !!(year && leagueTeamManagers.currentSeason
                            && String(year) !== String(leagueTeamManagers.currentSeason));

    $: teamTransactions = isFormerManager
        ? []
        : transactions.filter(t => t.rosters.includes(parseInt(rosterID)));

    /*
    Career totals come from the static dataset rather than the live API: Sleeper only exposes
    the podium and the toilet bowl, so a placement of 4th through 9th -- and therefore any
    honest "best finish" -- is not derivable from getAwards(). See helperFunctions/leagueHistory.
    Null for anyone missing from the history, which the markup guards on.
    */
    $: career = getManagerCareer(leagueHistory, viewManager.managerID);

    // ".572", the way a record is actually written, rather than "0.572".
    const pct = (n) => n === null || n === undefined ? null : n.toFixed(3).replace(/^0/, '');

    $: roster = rosters[rosterID];

    $: coOwners = year && rosterID ? leagueTeamManagers.teamManagersMap[year][rosterID].managers.length > 1 : roster.co_owners;

    $: commissioner = viewManager.managerID ? leagueTeamManagers.users[viewManager.managerID].is_owner : false;

    let players, playersInfo;
    let loading = true;

    const refreshTransactions = async () => {
        const newTransactions = await getLeagueTransactions(false, true);
        transactions = newTransactions.transactions;
    }

    onMount(async () => {
        if(transactionsData.stale) {
            refreshTransactions();
        }
        const playerData = await loadPlayers(null);
        playersInfo = playerData;
        players = playerData.players;
        loading = false;

        if(playerData.stale) {
            const newPlayerData = await loadPlayers(null, true);
            playersInfo = newPlayerData;
            players = newPlayerData.players;
        }
    })

    const changeManager = (newManager, noscroll = false) => {
        if(!newManager) {
            goto(`/managers`);
        }
        manager = newManager;
        goto(`/manager?manager=${newManager}`, {noscroll});
    }
</script>

<style>
    .managerContainer {
        width: 100%;
        margin: 2em 0 5em;
    }

    .managerConstrained {
        width: 97%;
        max-width: 800px;
        margin: 0 auto 4em;
    }

    .managerPhoto {
        display: block;
        border-radius: 100%;
        width: 70%;
        max-width: 200px;
        height: auto;
        margin: 5em auto 1em;
        box-shadow: 0 0 8px 4px #aaa;
    }

    h2 {
        text-align: center;
        font-size: 2.8em;
        margin: 1em 0 0em;
        line-height: 1em;
    }

    h3 {
        text-align: center;
        font-size: 1.5em;
        margin: 1.5em 0 0.5em;
        font-weight: 200;
    }

    .basicInfo {
        display: flex;
        justify-content: space-evenly;
        align-items: center;
        height: 24px;
        margin: 2em 0;
    }

    .basicInfo span {
        color: #888;
        font-size: 0.9em;
    }

    .infoChild {
        font-style: italic;
    }

    .infoContact {
        height: 20px;
        vertical-align: middle;
        padding-left: 1em;
    }

    .infoTeam {
        height: 48px;
    }

    .bio {
        margin: 2em 1.5em 2em;
        text-indent: 4em;
    }

    .philosophy {
        margin: 2em 1.5em 2em;
        text-indent: 4em;
    }

    .loading {
        display: block;
        width: 85%;
        max-width: 500px;
        margin: 80px auto;
    }

    .teamSub {
        font-size: 0.4em;
        line-height: 1em;
        color: #666;
    }

    .careerStats {
        margin: 2.5em 0 1em;
    }

    .careerHeading {
        font-family: var(--fontDisplay);
        font-size: 0.85em;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.16em;
        color: var(--g555);
        text-align: center;
        margin: 0 0 0.9em;
    }

    .statGrid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(112px, 1fr));
        gap: 0.6em;
    }

    .managerNav {
        margin: 4em 0 2em;
        text-align: center;
    }

    .upper {
        margin-top: 0;
    }

    .commissionerBadge {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 25px;
        width: 25px;
        font-weight: 600;
        border-radius: 15px;
        background-color: var(--blueTwo);
        border: 1px solid var(--blueOne);
    }

    .commissionerBadge span {
        font-style: normal;
        color: #fff;
    }

    /* media queries */

    @media (max-width: 505px) {
        :global(.selectionButtons span) {
            font-size: 0.8em;
        }
    }

    @media (max-width: 435px) {
        :global(.selectionButtons span) {
            line-height: 1.2em;
            font-size: 0.8em;
        }
    }

	@media (max-width: 450px) {

        .basicInfo {
            height: 20px;
        }

        .basicInfo span {
            font-size: 0.75em;
        }

        .infoTeam {
            height: 30px;
        }
	}

    @media (max-width: 370px) {

        .basicInfo {
            height: 18px;
        }

        .basicInfo span {
            font-size: 0.6em;
        }

        .infoTeam {
            height: 24px;
        }
    }
</style>

<div class="managerContainer">
    <div class="managerConstrained">
        <img class="managerPhoto" src="{viewManager.photo}" alt="{viewManager.name}"/>
        <h2>
            {viewManager.name}
            {#if teamName}
                <div class="teamSub">{coOwners ? 'Co-' : ''}Manager of <i>{teamName}</i></div>
            {/if}
        </h2>
        
        <div class="basicInfo">
            <span class="infoChild">{viewManager.location || 'Undisclosed Location'}</span>
            {#if viewManager.managerID && datesActive.start}
                <span class="seperator">|</span>
                {#if datesActive.end}
                    <span class="infoChild">In the league from '{datesActive.start.toString().substr(2)} to '{datesActive.end.toString().substr(2)}</span>
                {:else}
                    <span class="infoChild">In the league since '{datesActive.start.toString().substr(2)}</span>
                {/if}
            {:else if viewManager.fantasyStart}
                <!-- fantasyStart is an optional field -->
                <span class="seperator">|</span>
                <span class="infoChild">Playing ff since '{viewManager.fantasyStart.toString().substr(2)}</span>
            {/if}
            {#if viewManager.preferredContact}
                <!-- preferredContact is an optional field -->
                <span class="seperator">|</span>
                <span class="infoChild">{viewManager.preferredContact}<img class="infoChild infoContact" src="/{viewManager.preferredContact}.png" alt="preferred contact: {viewManager.preferredContact}"/></span>
            {/if}
            <!-- <span class="infoChild">{viewManager.preferredContact}</span> -->
            {#if viewManager.favoriteTeam}
                <!-- favoriteTeam is an optional field -->
                <span class="seperator">|</span>
                <img class="infoChild infoTeam" src="https://sleepercdn.com/images/team_logos/nfl/{viewManager.favoriteTeam}.png" alt="favorite team"/>
            {/if}
            {#if commissioner}
                <span class="seperator">|</span>
                <div class="infoChild commissionerBadge">
                    <span>C</span>
                </div>
            {/if}
        </div>

        {#if career && career.games}
            <div class="careerStats">
                <h3 class="careerHeading">Career Stats</h3>
                <div class="statGrid">
                    <StatTile label="Record" value={career.record} size="sm" />
                    <StatTile label="Win %" value={pct(career.winPct)} size="sm" />
                    <StatTile label="Points / Game" value={career.ppg.toFixed(1)} size="sm" />
                    <StatTile
                        label="Seasons"
                        value={career.seasonsPlayed}
                        size="sm"
                    />
                    <StatTile
                        label={career.championships === 1 ? 'Title' : 'Titles'}
                        value={career.championships}
                        size="sm"
                        tone={career.championships > 0 ? 'champion' : 'default'}
                    />
                    {#if career.best}
                        <StatTile
                            label="Best Finish"
                            value={ordinal(career.best.place)}
                            sub={career.best.season}
                            size="sm"
                            tone={career.best.place === 1 ? 'positive' : 'default'}
                        />
                    {/if}
                </div>
            </div>
        {/if}

        <div class="managerNav upper">
            <Group variant="outlined">
                {#if manager == 0}
                    <Button disabled class="selectionButtons" onclick={() => changeManager(parseInt(manager) - 1, true)} variant="outlined">
                        <Label>Previous Manager</Label>
                    </Button>
                {:else}
                    <Button class="selectionButtons" onclick={() => changeManager(parseInt(manager) - 1, true)} variant="outlined">
                        <Label>Previous Manager</Label>
                    </Button>
                {/if}
                <Button class="selectionButtons" onclick={() => goto('/managers')} variant="outlined">
                    <Label>All Managers</Label>
                </Button>
                {#if manager == managers.length - 1}
                    <Button disabled class="selectionButtons" onclick={() => changeManager(parseInt(manager) + 1, true)} variant="outlined">
                        <Label>Next Manager</Label>
                    </Button>
                {:else}
                    <Button class="selectionButtons" onclick={() => changeManager(parseInt(manager) + 1, true)} variant="outlined">
                        <Label>Next Manager</Label>
                    </Button>
                {/if}
            </Group>
        </div>

        <p class="bio">{@html viewManager.bio}</p>

        {#if viewManager.philosophy}
            <!-- philosophy is an optional field -->
            <h3>Team Philosophy</h3>
            <p class="philosophy">{@html viewManager.philosophy}</p>
        {/if}
    </div>

    {#if !loading}
        <!-- Favorite player -->
        <ManagerFantasyInfo {viewManager} {players} {changeManager} />
    {/if}

    <ManagerAwards {leagueTeamManagers} tookOver={viewManager.tookOver} {awards} {records} {rosterID} managerID={viewManager.managerID} />

    {#if loading}
        <!-- promise is pending -->
        <div class="loading">
            <p>Retrieving players...</p>
            <LinearProgress indeterminate />
        </div>
    {:else if !isFormerManager}
        <Roster division="1" expanded={false} {rosterPositions} {roster} {leagueTeamManagers} {players} {startersAndReserve} />
    {/if}

    {#if !isFormerManager}
    <h3>Team Transactions</h3>
    <div class="managerConstrained">
        {#if loading}
            <!-- promise is pending -->
            <div class="loading">
                <p>Retrieving players...</p>
                <LinearProgress indeterminate />
            </div>
        {:else}
            <TransactionsPage {playersInfo} transactions={teamTransactions} {leagueTeamManagers} show='both' query='' page={0} perPage={5} />
        {/if}
    </div>
    {/if}

    <div class="managerNav">
        <Group variant="outlined">
            {#if manager == 0}
                <Button disabled class="selectionButtons" onclick={() => changeManager(parseInt(manager) - 1)} variant="outlined">
                    <Label>Previous Manager</Label>
                </Button>
            {:else}
                <Button class="selectionButtons" onclick={() => changeManager(parseInt(manager) - 1)} variant="outlined">
                    <Label>Previous Manager</Label>
                </Button>
            {/if}
            <Button class="selectionButtons" onclick={() => goto('/managers')} variant="outlined">
                <Label>All Managers</Label>
            </Button>
            {#if manager == managers.length - 1}
                <Button disabled class="selectionButtons" onclick={() => changeManager(parseInt(manager) + 1)} variant="outlined">
                    <Label>Next Manager</Label>
                </Button>
            {:else}
                <Button class="selectionButtons" onclick={() => changeManager(parseInt(manager) + 1)} variant="outlined">
                    <Label>Next Manager</Label>
                </Button>
            {/if}
        </Group>
    </div>

</div>