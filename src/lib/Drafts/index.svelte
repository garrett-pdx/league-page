<script>
	import { waitForAll } from '$lib/utils/helper';
    import LinearProgress from '@smui/linear-progress';
    import { SectionHeading, Disclosure } from '$lib/Design';
    import Draft from './Draft.svelte';
    import { CARRIED_OVER_DRAFT_ID, FOUNDING_SEASON } from '$lib/Seasons/seasonData';

    export let upcomingDraftData, previousDraftsData, leagueTeamManagersData, playersData;

    // Sleeper marks a finished draft "complete", and getUpcomingDraft() answers that by PROJECTING
    // next year's board. That means we are in season: the draft that happened is the content, so
    // the projection folds away behind a control. Anything else (pre_draft, drafting) is a draft
    // that is still to come, and it is shown in full. Either way it sits above the previous
    // drafts -- a collapsed control at the bottom would sit under five boards and never be found.
</script>

<style>
	.loading {
		display: block;
		width: 85%;
		max-width: 500px;
		margin: 80px auto;
	}
</style>


{#await waitForAll(upcomingDraftData, leagueTeamManagersData, playersData) }
	<div class="loading">
		<p>Retrieving upcoming draft...</p>
		<br />
		<LinearProgress indeterminate />
	</div>
{:then [upcomingDraft, leagueTeamManagers, {players}] }
    {#if upcomingDraft.draftStatus == "complete"}
        <Disclosure label="Projected {upcomingDraft.year} draft order" openLabel="Hide projected {upcomingDraft.year} draft order">
            <Draft draftData={upcomingDraft} {leagueTeamManagers} year={upcomingDraft.year} {players} />
        </Disclosure>
    {:else}
        <SectionHeading level={3}>Upcoming {upcomingDraft.year} Draft</SectionHeading>
        <Draft draftData={upcomingDraft} {leagueTeamManagers} year={upcomingDraft.year} {players} />
    {/if}
{:catch error}
	<!-- promise was rejected -->
	<p>Something went wrong: {error.message}</p>
{/await}

{#await waitForAll(previousDraftsData, leagueTeamManagersData, playersData) }
	<SectionHeading level={3}>Previous Drafts</SectionHeading>
	<div class="loading">
		<p>Retrieving previous drafts...</p>
		<br />
		<LinearProgress indeterminate />
	</div>
{:then [previousDrafts, leagueTeamManagers, {players}] }
	<!-- Don't display anything unless there are previous drafts -->
	{#if previousDrafts.length}
		<SectionHeading level={3}>Previous Drafts</SectionHeading>
		{#each previousDrafts as previousDraft}
			<!-- Sleeper files the league's 2021 ESPN draft under 2022; it is not a second 2022 draft. -->
			<SectionHeading level={4} rule={false}>{previousDraft.draftID == CARRIED_OVER_DRAFT_ID ? `${FOUNDING_SEASON} Draft (ESPN, carried over)` : `${previousDraft.year} Draft`}</SectionHeading>
			<Draft draftData={previousDraft} previous={true} {leagueTeamManagers} year={previousDraft.year} {players} />
		{/each}
	{/if}
{:catch error}
	<!-- promise was rejected -->
	<p>Something went wrong: {error.message}</p>
{/await}
