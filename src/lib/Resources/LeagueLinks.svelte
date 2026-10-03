<script>
    import { leagueID, enableBlog } from '$lib/utils/helper';
    import { SectionHeading } from '$lib/Design';

    /*
    The league's own links, mounted first on /resources, above upstream's Resources.svelte
    (which stays untouched beneath it). League-owned on purpose: upstream's list is a generic
    set of paid sites and dynasty tools, and editing it would conflict on every release.

    "Useful elsewhere" is a short, hand-picked list for a half-PPR, $100-FAAB keeper league.
    Every entry was free and resolved when checked (2026-10-03). Two of them age:
      * the 4for4 waiver guide is the 2026 edition, at a URL with the year in it -- swap it for
        the new season's guide each preseason, or drop it;
      * the FantasyPros pages keep their URLs year to year and roll over by themselves.
    */
    const leagueLinks = [
        {
            name: 'Keeper Draft Board',
            note: 'Keeper costs, who everyone is keeping, and the draft room.',
            url: 'https://garrett-pdx.github.io/keeper-draft-board/',
            icon: 'grid_view',
        },
        {
            name: 'The league on Sleeper',
            note: 'Where lineups get set and trades get made.',
            url: `https://sleeper.app/leagues/${leagueID}`,
            icon: 'sports_football',
        },
        {
            name: 'Constitution',
            note: 'The rules, as voted. Seven votes change them.',
            url: '/constitution',
            icon: 'gavel',
        },
        {
            name: 'The Mudd Report',
            note: 'The Monday recap and the midweek preview.',
            url: '/blog',
            icon: 'article',
            blog: true,
        },
    ].filter((link) => !link.blog || enableBlog);

    const elsewhere = [
        {
            name: 'Half-PPR rankings: this week',
            note: 'FantasyPros expert consensus for RB, WR and TE.',
            url: 'https://www.fantasypros.com/nfl/rankings/half-point-ppr-flex.php',
            icon: 'leaderboard',
        },
        {
            name: 'Half-PPR rankings: rest of season',
            note: 'FantasyPros. Worth a look before a trade, or a keeper decision.',
            url: 'https://www.fantasypros.com/nfl/rankings/ros-half-point-ppr-overall.php',
            icon: 'trending_up',
        },
        {
            name: 'NFL injury report',
            note: "The league's official practice and game-status reports, from NFL.com.",
            url: 'https://www.nfl.com/injuries/',
            icon: 'healing',
        },
        {
            name: 'FAAB and the waiver wire',
            note: "4for4's 2026 waiver guide, with a section on spending a FAAB budget.",
            url: 'https://www.4for4.com/2026/preseason/ultimate-guide-winning-waiver-wire-2026',
            icon: 'payments',
        },
    ];

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

    <p class="groupCaption">Useful elsewhere</p>
    {@render linkList(elsewhere, 'Useful elsewhere')}
    <p class="disclaimer">All four are free to read.</p>
</section>
