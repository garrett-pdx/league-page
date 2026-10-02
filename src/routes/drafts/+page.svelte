<script>
	import { Drafts } from '$lib/components';
	import { PageHeader } from '$lib/Design';

    export let data;
    const {upcomingDraftData, previousDraftsData, leagueTeamManagersData, playersData} = data;
</script>

<style>
    #main {
        position: relative;
        z-index: 1;
    }
</style>

<PageHeader title="Drafts" intro="Every draft on record, keepers badged. None of it can be undone." />

<div id="main">
	<Drafts {upcomingDraftData} {previousDraftsData} {leagueTeamManagersData} {playersData} />
</div>