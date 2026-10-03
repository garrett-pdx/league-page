import { findTab } from '$lib/utils/tabs';

/*
The browser tab title, minus the " | League Name" suffix that Nav/index.svelte appends.
Ours, not upstream's: upstream's one-line expression capitalised the URL path, so /awards was
titled "Awards" under a nav that says "Trophy Room", every manager page was just "Manager", and
a blog post was "Blog/2026-week-4-preview".

Order of preference:
  0. an error page is "Not found" (404) or "Error", never the path: a bad URL such as
     /seasons/1999 would otherwise borrow the Seasons label;
  1. `page.data.title`, when the route's load() returned one (/manager, /blog/[slug]);
  2. the nav label from tabs.js, matched on the path (aliases included, so /manager without a
     title still reads "Managers");
  3. upstream's behaviour: the path with its first letter capitalised.
*/
export const pageTitle = (page) => {
    if(page.error) return page.status == 404 ? 'Not found' : 'Error';
    if(page.data?.title) return page.data.title;
    const path = page.url.pathname;
    if(path == '/' || path == '') return 'Home';
    const [tab, child] = findTab(path);
    if(child) return child.label;
    if(tab) return tab.label;
    return path[1].toUpperCase() + path.slice(2);
}

// "2026-week-4-preview" -> "2026 Week 4 Preview". Blog posts get their title from Contentful,
// which is async, and awaiting it in load() would hold the whole page; the slug is near enough.
// Posts shared before slugs existed are addressed by their Contentful entry id, which has no
// hyphens and reads as noise, so those fall back to plain "Blog".
export const titleFromSlug = (slug) => {
    if(!slug || !slug.includes('-')) return 'Blog';
    return slug
        .split('-')
        .filter(Boolean)
        .map(word => word[0].toUpperCase() + word.slice(1))
        .join(' ');
}
