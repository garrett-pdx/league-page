<script>
    import { onMount } from "svelte";
	import LinearProgress from '@smui/linear-progress';
    import Post from "./Post.svelte";
    import { getBlogPosts, getLeagueTeamManagers, waitForAll, blogTitle } from "$lib/utils/helper";

    const lang = "en-US";

    let post;
    let createdAt;
    let id;
    let loading = true;
    let leagueTeamManagers = {};
    // True once loading finds no post at all; the home page hides the block (bind:empty).
    export let empty = false;

    // The featured post, else the newest one (posts arrive newest first).
    const pick = (posts) => {
        const chosen = posts.find((p) => p.fields.featured) || posts[0];
        if(!chosen) return;
        createdAt = chosen.sys.createdAt;
        post = chosen.fields;
        id = chosen.sys.id;
    };

    onMount(async() => {
        const [{posts, fresh}, leagueTeamManagersData] = await waitForAll(getBlogPosts(null), getLeagueTeamManagers());
		leagueTeamManagers = leagueTeamManagersData;
        pick(posts);

        if(!fresh) {
		    const {posts} = await getBlogPosts(null, true);
            pick(posts);
        }

        empty = !post;
        loading = false;
    })
</script>

<style>
    .loading {
        display: block;
        width: 85%;
        max-width: 500px;
        margin: 80px auto;
    }

    h2 {
        font-size: 2em;
        text-align: center;
        margin-bottom: 1.5em;
    }

    .center {
        text-align: center;
        margin-bottom: 2em;
    }

    .viewAll {
        display: inline-flex;
        align-items: center;
        min-height: 44px;
        box-sizing: border-box;
        text-decoration: none;
        background-color: var(--emblem);
        color: #fff;
        border-radius: 1em;
        padding: 0.5em 1em;
    }

    .viewAll:hover {
        background-color: var(--emblem);
    }
</style>

{#if loading}
    <!-- promise is pending -->
    <div class="loading">
        <p>Loading Blog Posts...</p>
        <LinearProgress indeterminate />
    </div>
{:else if post}
    <h2>{blogTitle}</h2>
    <Post {leagueTeamManagers} {post} {createdAt} {id} />
    <div class="center">
        <a class="viewAll" href="/blog">View More Blog Posts</a>
    </div>
{/if}