<script>
    import { league, leagueLinks, elsewhereLinks } from '$lib/utils/helper';
    import { SectionHeading } from '$lib/Design';

    /*
    The league's own links, mounted first on /resources, above the generic Resources.svelte.
    Both lists come from league.json (links.league and links.elsewhere): the league's tools and
    pages first, then a short, hand-picked list of outside resources suited to its format.
    Links with a year in the URL go stale; the preseason checklist says to re-check them.
    */
    const isExternal = (url) => /^https?:\/\//.test(url);
</script>

<style>
    .leagueLinks {
        position: relative;
        z-index: 1;
    }

    .card {
        width: 90%;
        max-width: var(--pageMaxText);
        margin: 15px auto;
        padding: 0;
        list-style: none;
        background-color: var(--fff);
        border: 1px solid var(--accentBorder);
        border-radius: var(--radiusSm);
        box-shadow: var(--shadowCard);
        overflow: hidden;
    }

    .card li + li {
        border-top: 1px solid var(--ddd);
    }

    .link {
        display: flex;
        align-items: center;
        gap: 16px;
        min-height: 56px;
        padding: 10px 16px;
        box-sizing: border-box;
        color: inherit;
        text-decoration: none;
    }

    @media (hover: hover) {
        .link:hover {
            background-color: var(--navy050);
        }
    }

    .link:focus-visible {
        outline: 2px solid var(--accentInk);
        outline-offset: -2px;
    }

    .icon {
        flex-shrink: 0;
        color: var(--accentInk);
    }

    .text {
        flex-grow: 1;
        min-width: 0;
    }

    .name {
        display: block;
        font-size: 1.05em;
        font-weight: 500;
        color: var(--navy700);
    }

    .note {
        display: block;
        font-size: 0.9em;
        color: var(--g555);
        margin-top: 2px;
    }

    .external {
        flex-shrink: 0;
        font-size: 18px;
        color: var(--g555);
    }

    .groupCaption {
        width: 90%;
        max-width: var(--pageMaxText);
        margin: 28px auto 0;
        font-family: var(--fontDisplay);
        font-size: 0.85em;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.16em;
        color: var(--g555);
    }

    .disclaimer {
        width: 90%;
        max-width: var(--pageMaxText);
        margin: 0 auto;
        font-size: 0.9em;
        color: var(--g555);
        text-align: center;
    }

    .srOnly {
        position: absolute;
        width: 1px;
        height: 1px;
        overflow: hidden;
        clip: rect(0 0 0 0);
        white-space: nowrap;
    }
</style>

{#snippet linkList(links, label)}
    <ul class="card" aria-label={label}>
        {#each links as link}
            <li>
                <a
                    class="link"
                    href={link.url}
                    target={isExternal(link.url) ? '_blank' : null}
                    rel={isExternal(link.url) ? 'noopener noreferrer' : null}
                >
                    <span class="material-icons icon" aria-hidden="true">{link.icon}</span>
                    <span class="text">
                        <span class="name">{link.name}{#if isExternal(link.url)}<span class="srOnly"> (opens in a new tab)</span>{/if}</span>
                        <span class="note">{link.note}</span>
                    </span>
                    {#if isExternal(link.url)}
                        <span class="material-icons external" aria-hidden="true">open_in_new</span>
                    {/if}
                </a>
            </li>
        {/each}
    </ul>
{/snippet}

<section class="leagueLinks">
    <SectionHeading level={3}>League links</SectionHeading>
    {@render linkList(leagueLinks, 'League links')}

    {#if elsewhereLinks.length}
        <p class="groupCaption">Useful elsewhere</p>
        {@render linkList(elsewhereLinks, 'Useful elsewhere')}
        {#if league.links?.elsewhereNote}<p class="disclaimer">{league.links.elsewhereNote}</p>{/if}
    {/if}
</section>
