<script>
    /*
    A season played before the league came to Sleeper (league.json history.preSleeper). What
    survives of it is whatever the league wrote down -- the story -- plus, if the league imported
    its draft into Sleeper, that draft: Sleeper files it under the first Sleeper season as a
    second, non-primary draft, dated the day it was imported rather than the day it was held.
    No standings, matchups, transactions or champion exist in Sleeper for it, and this page says
    so rather than guessing.
    */
    import { managers } from '$lib/utils/leagueInfo';
    import { SectionHeading, Disclosure } from '$lib/Design';
    import DraftRounds from './DraftRounds.svelte';
    import { importedDraft, earlyRounds, peopleLookup } from './seasonData';

    export let pre;
    export let history;
    export let playersData;

    const people = peopleLookup(history, managers);
    const draft = importedDraft(history, pre);
    const all = earlyRounds(draft, draft?.rounds || 0);
    // Teams in the draft = distinct draft slots, which holds whatever season Sleeper filed it under.
    const teams = draft ? new Set(draft.picks.map((p) => p.draft_slot)).size : 0;
</script>

<style>
    .story {
        width: 92%;
        max-width: var(--pageMaxText);
        margin: 0 auto 1.5rem;
        padding: 1.1rem 1.3rem;
        box-sizing: border-box;
        background-color: var(--fff);
        border-radius: var(--radiusMd);
        box-shadow: var(--shadowCard);
        color: var(--g333);
        line-height: 1.55;
    }

    .story :global(p) { margin: 0 0 0.8em; }
    .story :global(p:last-child) { margin-bottom: 0; }

    .story :global(a) {
        color: var(--accentInk);
        display: inline-block;
        padding: 0.7em 0;
        margin: -0.7em 0;
    }

    .missing {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 0.6rem;
        width: 92%;
        max-width: var(--pageMaxText);
        margin: 0 auto 1rem;
        padding: 0;
        list-style: none;
    }

    .missing li {
        padding: 0.7rem 0.9rem;
        border: 1px dashed var(--accentBorder);
        border-radius: var(--radiusMd);
        color: var(--g555);
        text-align: center;
    }

    .missing strong {
        display: block;
        font-family: var(--fontDisplay);
        font-weight: 500;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--g444);
    }

    .note {
        text-align: center;
        color: var(--g555);
        margin: 0 auto 1.2em;
        max-width: 36em;
        width: 92%;
        line-height: 1.45;
    }

    .loading { min-height: 80vh; text-align: center; color: var(--g555); }
</style>

{#if pre.story}
    <div class="story">{@html pre.story}</div>
{/if}

<ul class="missing" aria-label="What did not survive">
    <li><strong>Standings</strong>none on record</li>
    <li><strong>Results</strong>none on record</li>
    <li><strong>Champion</strong>unknown</li>
</ul>

{#if draft}
    <SectionHeading level={3} eyebrow="{draft.rounds} rounds · snake">The {pre.season} draft</SectionHeading>
    <p class="note">{pre.draftNote || 'As imported into Sleeper.'}</p>
    {#await playersData}
        <p class="loading">Loading the draft...</p>
    {:then players}
        <DraftRounds rounds={all.slice(0, 3)} {teams} {players} {people} />
        <Disclosure label="Show rounds 4–{draft.rounds}" openLabel="Hide rounds 4–{draft.rounds}">
            <DraftRounds rounds={all.slice(3)} {teams} {players} {people} />
        </Disclosure>
    {:catch error}
        <p class="note">The draft wouldn't load: {error.message}</p>
    {/await}
{/if}
