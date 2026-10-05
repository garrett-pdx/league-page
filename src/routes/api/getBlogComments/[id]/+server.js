import contentful from 'contentful';
import { json, error } from '@sveltejs/kit';
import { contentfulTypes } from '$lib/utils/helper';


export async function GET({params}) {
    if(!import.meta.env.VITE_CONTENTFUL_CLIENT_ACCESS_TOKEN) {
        throw error(500, "Missing VITE_CONTENTFUL_CLIENT_ACCESS_TOKEN: Contentful comments need it (see docs/setup.md, \"The blog\")");
    }
    const client = contentful.createClient({
        // This is the space ID. A space is like a project folder in Contentful terms
        space: import.meta.env.VITE_CONTENTFUL_SPACE,
        // This is the access token for this space. Normally you get both ID and the token in the Contentful web app
        accessToken: import.meta.env.VITE_CONTENTFUL_CLIENT_ACCESS_TOKEN
    });
    const blogID = params.id;
	// Not upstream's hardcoded 'blog_comment' -- see contentfulTypes in leagueInfo.js.
	const data = await client.getEntries({content_type: contentfulTypes.comment,'fields.blogID': blogID})
        .catch(e => {
            console.error(e);
            throw error(500, "Problem retrieving blog comments");
        });

    return json(data);
}