<script>
    /*
    A manager's photo and name, linking to their page. Names and photos come from leagueInfo's
    `managers` (through peopleLookup in seasonData.js), not from Sleeper, so a history page
    renders without waiting on the Sleeper walk and a departed manager still has a name.

        <Person person={people[uid]} />

    `size` is the photo in px; `short` shows the first name only, for tight cells.
    */
    export let person;
    export let size = 28;
    export let short = false;
    export let link = true;
</script>

<style>
    .person {
        display: inline-flex;
        align-items: center;
        gap: 0.45em;
        min-width: 0;
        color: inherit;
        text-decoration: none;
        vertical-align: middle;
    }

    /* 44px tall so it is a real tap target, whatever the photo size */
    a.person { color: var(--accentInk); min-height: 44px; }

    @media (hover: hover) {
        a.person:hover .name { text-decoration: underline; }
    }

    a.person:focus-visible {
        outline: 2px solid var(--blueOne);
        outline-offset: 2px;
        border-radius: var(--radiusXs);
    }

    img, .blank {
        flex-shrink: 0;
        border-radius: var(--radiusCircle);
        object-fit: cover;
        background-color: var(--navy050);
    }

    .name {
        overflow-wrap: anywhere;
        line-height: 1.15;
    }
</style>

<svelte:element
    this={link && person?.href ? 'a' : 'span'}
    href={link && person?.href ? person.href : undefined}
    class="person"
>
    {#if person?.photo}
        <img src={person.photo} alt="" width={size} height={size} style="width: {size}px; height: {size}px;" loading="lazy" />
    {:else}
        <span class="blank" style="width: {size}px; height: {size}px;" aria-hidden="true"></span>
    {/if}
    <span class="name">{short ? person?.first : person?.name ?? 'Unknown'}</span>
</svelte:element>
