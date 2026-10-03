<script>
    /*
    2021, the founding season, played on ESPN. Only the draft came across to Sleeper: it is the
    non-primary draft filed under 2022 in league-history.json (carriedOverDraft()), dated the day
    it was imported rather than the day it was held. No standings, matchups, transactions or
    champion survive, and this page says so rather than guessing.
    */
    import { waitForAll } from '$lib/utils/helper';
    import { managers } from '$lib/utils/leagueInfo';
    import { SectionHeading, Disclosure } from '$lib/Design';
    import DraftRounds from './DraftRounds.svelte';
    import { carriedOverDraft, earlyRounds, peopleLookup } from './seasonData';

    export let history;
    export let playersData;

    const people = peopleLookup(history, managers);
    const draft = carriedOverDraft(history);
    const all = earlyRounds(draft, draft?.rounds || 0);
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

    .story p { margin: 0 0 0.8em; }
    .story p:last-child { margin-bottom: 0; }

    .story a {
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

<div class="story">
    <p>
        The Mudd League started in 2021 on ESPN: ten teams, run by a group of friends, several of
        whom had played football together at Claremont-Mudd-Scripps. After one season it moved to Sleeper, and
        only one thing made the trip: the draft.
    </p>
    <p>
        Sleeper filed that draft under the 2022 league, which is where it still lives. It was the
        baseline for every 2022 keeper price, since a keeper costs the round he went in the year
        before. The <a href="/seasons/2022">2022 page</a> lists those keepers and what they cost.
    </p>
    <p>
        Nothing else survives. There are no standings, scores, trades or champion from 2021, and
        anyone who claims to have won it is relying on everyone else's memory.
    </p>
</div>

<ul class="missing" aria-label="What did not survive">
    <li><strong>Standings</strong>none on record</li>
    <li><strong>Results</strong>none on record</li>
    <li><strong>Champion</strong>unknown</li>
</ul>

{#if draft}
    <SectionHeading level={3} eyebrow="{draft.rounds} rounds · snake">The 2021 draft</SectionHeading>
    <p class="note">As imported into Sleeper. Jordan Leonard, who played through 2022 before Brenden Brown took his spot, drafted from slot 8.</p>
    {#await playersData}
        <p class="loading">Loading the draft...</p>
    {:then players}
        <DraftRounds rounds={all.slice(0, 3)} teams={history.seasons?.['2022']?.teams || 10} {players} {people} />
        <Disclosure label="Show rounds 4–{draft.rounds}" openLabel="Hide rounds 4–{draft.rounds}">
            <DraftRounds rounds={all.slice(3)} teams={history.seasons?.['2022']?.teams || 10} {players} {people} />
        </Disclosure>
    {:catch error}
        <p class="note">The draft wouldn't load: {error.message}</p>
    {/await}
{/if}
