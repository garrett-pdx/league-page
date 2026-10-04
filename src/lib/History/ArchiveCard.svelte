<script>
    import { Card, SectionHeading } from '$lib/Design';
    import { managerHref } from '$lib/utils/managerLink';

    /*
    "From the archives" on the Trophy Room, mounted from routes/awards/+page.svelte between the
    Hall of Fame and the year-by-year podiums.

    Static on purpose: the facts are hand-written in league/archive-facts.json, with every figure
    re-derived from static/data/ at the time of writing. Nothing is fetched here --
    narratives.json is an authoring aid and too big to ship -- so the card has no loading state
    and arrives in the same paint as the Hall of Fame above it. A league without the file, or
    with an empty list, gets no card.

    Each fact is { label, text, season, managers, source }:
      label     the small kicker above the fact
      text      an array of segments, rendered in order:
                  "plain string"
                  { "m": "<user_id>", "label": "Kabroa" }   -> link to that manager's page
                  { "season": 2022 }                         -> link to /seasons/2022
                Segments rather than an HTML string, so nothing here is {@html}-injected.
      season    the season(s) the fact belongs to
      managers  user_ids named in it
      source    where the numbers come from, for whoever re-checks them

    Rules that keep a fact from going stale mid-season: completed seasons only, or a fixed
    historic event; any "most" or "widest" scoped "through <last completed season>"; and none
    that repeats a manager bio. Re-check them all at the end of each season.

    Links are inline in prose, so the 44px tap-target rule does not apply to them.
    */
    let { leagueTeamManagers } = $props();

    // Optional file: a glob rather than an import, so a league without one still builds.
    const files = import.meta.glob('$league/archive-facts.json', { eager: true, import: 'default' });
    const archiveFacts = Object.values(files)[0] || [];

    // The fact's own season decides whose roster a manager link resolves through; managerID
    // matches first, so this only matters for a manager missing from leagueInfo.
    const hrefFor = (seg, fact) => managerHref({ leagueTeamManagers, managerID: seg.m, year: Math.max(...fact.season) });
</script>

<style>
    .archive {
        display: block;
        width: 95%;
        max-width: var(--pageMax);
        margin: 0 auto 4em;
    }

    .facts {
        list-style: none;
        margin: 0;
        padding: 0;
        display: grid;
        grid-template-columns: 1fr;
        column-gap: 2.5em;
    }

    @media (min-width: 760px) {
        .facts { grid-template-columns: 1fr 1fr; }
    }

    .fact {
        padding: 1em 0;
        border-top: 1px solid var(--accentBorder);
        min-width: 0;
    }

    /* First row has no rule above it: one item on a phone, two side by side from 760px. */
    .fact:first-child { border-top: none; padding-top: 0.25em; }
    @media (min-width: 760px) {
        .fact:nth-child(2) { border-top: none; padding-top: 0.25em; }
    }

    .label {
        display: block;
        font-family: var(--fontDisplay);
        font-size: 0.8rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        line-height: 1.2;
        color: var(--g555);
        margin: 0 0 0.4em;
    }

    .text {
        margin: 0;
        font-size: 1rem;
        line-height: 1.55;
        font-variant-numeric: tabular-nums;
        overflow-wrap: anywhere;
    }

    .text a {
        color: var(--accentInk);
        text-decoration: underline;
        text-underline-offset: 2px;
        text-decoration-thickness: 1px;
    }

    .text a:hover { text-decoration-thickness: 2px; }

    .text a:focus-visible {
        outline: 2px solid var(--blueOne);
        outline-offset: 2px;
        border-radius: 2px;
    }
</style>

{#if archiveFacts.length}
<SectionHeading level={3} accent="navy">From the archives</SectionHeading>

<div class="archive">
    <Card elevation="raised" accent="navy" padding="md">
        <ul class="facts">
            {#each archiveFacts as fact (fact.label)}
                <li class="fact">
                    <span class="label">{fact.label}</span>
                    <p class="text">{#each fact.text as seg}{#if typeof seg === 'string'}{seg}{:else if seg.m}<a href={hrefFor(seg, fact)}>{seg.label}</a>{:else if seg.season}<a href="/seasons/{seg.season}">{seg.season}</a>{/if}{/each}</p>
                </li>
            {/each}
        </ul>
    </Card>
</div>
{/if}
