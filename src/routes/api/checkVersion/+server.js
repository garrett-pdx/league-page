import { version } from '$lib/version';
import { project } from '$lib/project';
import { json } from '@sveltejs/kit';

/*
Is a newer engine published? Compares this site's version with the template repository's
package.json on GitHub. Any failure (offline, rate-limited, renamed) answers "no update": the
check must never break a page. Cached for a day at the CDN, so it is one request a day, not one
per visitor.
*/
const newer = (a, b) => {
    const pa = String(a).split('.').map(Number), pb = String(b).split('.').map(Number);
    for(let i = 0; i < 3; i++) {
        if((pa[i] || 0) !== (pb[i] || 0)) return (pa[i] || 0) > (pb[i] || 0);
    }
    return false;
};

export async function GET({ setHeaders }) {
    setHeaders({ 'cache-control': 'public, max-age=3600, s-maxage=86400' });
    let needsUpdate = false;
    try {
        const res = await fetch(`https://raw.githubusercontent.com/${project.repo}/main/package.json`, { signal: AbortSignal.timeout(5000) });
        if(res.ok) needsUpdate = newer((await res.json()).version, version);
    } catch {
        // offline or unreachable: say nothing
    }
    return json(needsUpdate);
}
