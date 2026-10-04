<script>
	import { Drafts } from '$lib/components';
	import { PageHeader } from '$lib/Design';
	import { pageIntro } from '$lib/utils/leagueInfo';

    export let data;
    const {upcomingDraftData, previousDraftsData, leagueTeamManagersData, playersData} = data;
</script>

<style>
    #main {
        position: relative;
        z-index: 1;
    }
</style>

<PageHeader title="Drafts" intro={pageIntro('drafts')} />

<div id="main">
	<Drafts {upcomingDraftData} {previousDraftsData} {leagueTeamManagersData} {playersData} />
</div>