import contentful from 'contentful';
import { json, error } from '@sveltejs/kit';
import { contentfulTypes, blogBackend } from '$lib/utils/helper';
import { postsFromFiles } from '$lib/utils/blogMarkdown';

// The markdown backend's posts, bundled at build time: publishing a post is committing a file.
const postFiles = import.meta.glob('$league/posts/*.md', { eager: true, query: '?raw', import: 'default' });

export async function GET() {
    if(blogBackend === 'markdown') {
        const { items, errors } = postsFromFiles(postFiles);
        for(const e of errors) console.error(`league/posts: ${e}`);
        return json({ items });
    }
    if(blogBackend !== 'contentful') {
        return json({ items: [] });
    }

    if(!import.meta.env.VITE_CONTENTFUL_CLIENT_ACCESS_TOKEN) {
        throw error(500, "blog.backend is \"contentful\" but VITE_CONTENTFUL_CLIENT_ACCESS_TOKEN is not set; set it (and VITE_CONTENTFUL_SPACE), or switch blog.backend to \"markdown\" in league/league.json");
    }
    const client = contentful.createClient({
        // This is the space ID. A space is like a project folder in Contentful terms
        space: import.meta.env.VITE_CONTENTFUL_SPACE,
        // This is the access token for this space. Normally you get both ID and the token in the Contentful web app
        accessToken: import.meta.env.VITE_CONTENTFUL_CLIENT_ACCESS_TOKEN
    });
	// Content type IDs are configuration: blog.contentful in league.json.
	const data = await client.getEntries({content_type: contentfulTypes.post})
        .catch(e=> {
            console.error(e);
            throw error(500, "Problem retrieving blog posts");
        });

    return json(data);
}
