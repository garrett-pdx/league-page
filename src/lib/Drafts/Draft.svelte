<script>
  	import DataTable, { Head, Body, Row, Cell } from '@smui/data-table';
	import LinearProgress from '@smui/linear-progress';
    import { onMount } from 'svelte';
    import DraftRow from './DraftRow.svelte';
    import { gotoManager } from '$lib/utils/helper'
	import { getAvatarFromTeamManagers, getTeamNameFromTeamManagers } from '$lib/utils/helperFunctions/universalFunctions';
    
    export let draftData, leagueTeamManagers, previous = false, year, players;

    const {draftOrder, draft, accuracy, reversalRound, draftType} = draftData;

    let progress = 0;
    let closed = false;

    onMount(loadAccuracy);

    function loadAccuracy() {
        if(!accuracy || accuracy === 1) return;
        let timer;
        progress = 0;
        closed = false;
        clearInterval(timer);
        timer = setInterval(() => {
            progress += 0.02;
            if (progress >= accuracy) {
                clearInterval(timer);
                if (progress >= 1) {
                    progress = 1;
                    closed = true;
                }
            }

        }, 100);
    }
</script>

<style>
    .accuracy {
        display: block;
        width: 80%;
        max-width: 800px;
        margin: 2em auto 3em;
    }

    .accuracyText {
        font-size: 0.8em;
        color: var(--g555);
    }

    .disclaimer {
        font-style: italic;
        color: var(--g555);
    }

    /*
    The board is 1200px wide and fourteen rounds tall, so on a phone you are looking at roughly
    three of ten columns through a moving window. Two things make that navigable.

    The wrapper owns a right-edge fade, which is the only signal that more teams exist off-screen.
    It has to sit OUTSIDE the scrolling element or it scrolls away with the content.

    The board itself becomes a scroll region in both axes with a capped height, so the team header
    can stick. That cap is load-bearing rather than cosmetic: `overflow-x: auto` already forces
    overflow-y to compute to auto, so the board is a scroll container whether we like it or not,
    and `position: sticky` on the header resolves against IT, not the viewport. Without a height
    cap the container never scrolls vertically, so the header would never stick to anything while
    the page scrolled past it.
    */
    .boardWrap {
        position: relative;
        width: 95%;
        margin: 2em auto 3em;
    }

    .boardWrap::after {
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        width: 2.5em;
        height: 100%;
        pointer-events: none;
        background: linear-gradient(to right, rgba(255, 255, 255, 0), var(--fff));
        border-radius: 0 var(--radiusMd) var(--radiusMd) 0;
    }

    :global(.draftBoard) {
        display: block;
        width: 100%;
        margin: 0;
        border-radius: var(--radiusMd);
        box-shadow: var(--shadowCard);
    }

    /*
    The height cap belongs HERE, not on .draftBoard. SMUI renders the DataTable as an outer
    div (.draftBoard) wrapping .mdc-data-table__table-container, and it is that inner element
    which already carries MDC's own overflow-x: auto -- so it, not our wrapper, is the element
    the table actually overflows. Sticky resolves against the nearest scrollport, so capping the
    outer div made it scroll vertically while the header went on resolving against the uncapped
    inner one and never stuck. Capping the inner element gives the header something to stick to
    and keeps both axes on a single scroller.
    */
    :global(.draftBoard .mdc-data-table__table-container) {
        max-height: 70vh;
        overflow: auto;
    }

	:global(.draftTeam) {
        font-size: 0.8em;
		text-align: center;
		padding: 5px 0;
		background-color: var(--transactHeader);
        white-space: break-spaces;
        /* Team names are frequently one long unbroken word -- JustHereSoIWon'tGetFined,
           StepBurrow I'm Stuck -- which break-spaces alone will not wrap, so they clipped. */
        overflow-wrap: anywhere;
        line-height: 1em;
        height: 5em;
        vertical-align: initial;
        /* Sticky against the board's own scroll box. Needs an opaque background, which the
           --transactHeader fill above provides, and a stacking order above the body cells. */
        position: sticky;
        top: 0;
        z-index: 2;
	}

	:global(.draftBoard table) {
        /* MUST be separate, not collapse. Chrome does not honour position: sticky on a <th>
           inside a table with border-collapse: collapse -- the header computes as sticky and
           then scrolls away regardless, which is exactly what happened here. border-spacing 0
           keeps the cells flush, so this is visually identical to collapse for our borders
           (only right borders are set, so nothing doubles up). */
        border-collapse: separate;
        border-spacing: 0;
        table-layout: fixed;
        width: 100%;
        min-width: 1200px;
	}

    :global(.draftBoard td) {
        border-right: 1px solid var(--ddd);
        height: 7em;
        font-size: 0.7em;
    }

    :global(.draftBoard td:last-of-type) {
        border-right: none;
    }

	.avatar {
		border-radius: 50%;
        height: 30px;
        width: 30px;
        margin: 0.4em 0;
		border: 0.25px solid var(--g999);
	}

    .clickable {
        cursor: pointer;
    }
	
	:global(.curDraftName) {
        color: var(--g555);
        font-size: 0.8em;
        font-style: italic;
    }
</style>

{#if accuracy && accuracy !== 1 && !closed}
    <div class="accuracy">
        <div class="accuracyText">
            Upcomig draft order accuracy: {parseInt(progress*100)}%
            <span class="disclaimer">(accuracy will improve as the regular season progresses)</span>
        </div>
        <LinearProgress {progress} {closed} />
    </div>
{/if}

<div class="boardWrap">
<DataTable class="draftBoard">
    <Head>
        <Row>
            {#each draftOrder as draftPosition}
                {#if draftPosition}
                    <Cell class="draftTeam">
                        <img class="avatar clickable" onclick={() => gotoManager({year, leagueTeamManagers, rosterID: draftPosition})} src="{getAvatarFromTeamManagers(leagueTeamManagers, draftPosition, year)}" alt="{getTeamNameFromTeamManagers(leagueTeamManagers, draftPosition, year)} avatar"/>
                        <br />
                        <span class="clickable" onclick={() => gotoManager({year, leagueTeamManagers, rosterID: draftPosition})}>{getTeamNameFromTeamManagers(leagueTeamManagers, draftPosition, year)}{@html getTeamNameFromTeamManagers(leagueTeamManagers, draftPosition, year) != getTeamNameFromTeamManagers(leagueTeamManagers, draftPosition) ? `<br /><span class="curDraftName">(${getTeamNameFromTeamManagers(leagueTeamManagers, draftPosition)})</span>` : ''}</span>
                    </Cell>
                {/if}
            {/each}
        </Row>
    </Head>
    <Body>
        {#each draft as draftRow, row}
            <DraftRow {draftRow} row={row + 1} {previous} {reversalRound} {draftType} {players} {leagueTeamManagers} {year} />
        {/each}
    </Body>
</DataTable>
</div>

