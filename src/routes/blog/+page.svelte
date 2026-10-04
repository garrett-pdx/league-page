<script>
    import { Posts } from "$lib/components";
    import { blogTitle, blogIntro } from "$lib/utils/helper";
	import { PageHeader } from '$lib/Design';

    export let data;
    const {postsData, queryPage, filterKey, leagueTeamManagersData} = data;
</script>

<style>
    #main {
        position: relative;
        z-index: 1;
        display: block;
        margin: 30px auto;
		width: 95%;
		max-width: 1000px;
        overflow-y: hidden;
    }
</style>

<PageHeader title={blogTitle} intro={blogIntro} />

<div id="main">
    <Posts {postsData} {queryPage} {filterKey} {leagueTeamManagersData} />
</div>