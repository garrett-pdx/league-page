<script>
    import { PageHeader } from '$lib/Design';
    import { pageIntro } from '$lib/utils/leagueInfo';
    import SeasonsIndex from '$lib/Seasons/SeasonsIndex.svelte';

    export let data;
    const {historyData, gamesData, notesData} = data;
</script>

<PageHeader title="Seasons" intro={pageIntro('seasons')} />

<SeasonsIndex {historyData} {gamesData} {notesData} />
