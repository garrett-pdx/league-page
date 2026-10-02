
import { enableBlog, getBlogPosts, getLeagueTeamManagers } from '$lib/utils/helper';
import { titleFromSlug } from '$lib/utils/pageTitle';

export function load({ fetch, params }) {
    if(!enableBlog) return false;
    
    const postID = params.slug;
    const postsData = getBlogPosts(fetch);
    const leagueTeamManagersData = getLeagueTeamManagers();

    return {
        postsData,
        postID,
        leagueTeamManagersData,
        // Ours: the browser tab title, from the slug rather than the async Contentful title.
        title: titleFromSlug(postID),
    };
}