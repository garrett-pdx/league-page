<script>
    import { PageHeader } from '$lib/Design';
    import SeasonsIndex from '$lib/Seasons/SeasonsIndex.svelte';

    export let data;
    const {historyData, gamesData, notesData} = data;
</script>

<PageHeader title="Seasons" intro="Every season since the 2021 founding, one page each. The results are final; the arguments are not." />

<SeasonsIndex {historyData} {gamesData} {notesData} />
