<script>
    /*
    A row of team-name chips at the top of Rosters, each jumping to that team's roster further
    down. Ten rosters is about 6,500px of scrolling on a phone; this is the table of contents.

    Ours, mounted in routes/rosters/+page.svelte so Rosters.svelte and RosterSorter.svelte stay
    as upstream has them. The targets are the `id="team-<rosterID>"` on Roster.svelte's .team
    wrapper, which carries a scroll-margin-top so a jump lands below the sticky phone bar.

    The links are plain #hash anchors: SvelteKit leaves them to the browser, so they work with
    the keyboard, open nothing new, and a Cmd-click copies a link to that team.
    */
    export let rosters, leagueTeamManagers;

    const teams = Object.values(rosters).map((roster) => {
        const team = leagueTeamManagers.teamManagersMap[leagueTeamManagers.currentSeason]?.[roster.roster_id]?.team;
        return {
            id: roster.roster_id,
            name: team?.name ?? 'No Manager',
            avatar: team?.avatar ?? 'https://sleepercdn.com/images/v2/icons/player_default.webp',
        };
    });
</script>

<style>
    .chips {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 0.5em;
        width: 94%;
        max-width: var(--pageMax);
        margin: 0 auto;
        padding: 0;
        list-style: none;
    }

    .chip {
        display: inline-flex;
        align-items: center;
        gap: 0.5em;
        min-height: 44px;
        box-sizing: border-box;
        padding: 0 1em 0 0.4em;
        border: 1px solid var(--accentBorder);
        border-radius: var(--radiusPill);
        background-color: var(--fff);
        color: var(--navy700);
        font-size: 0.9em;
        line-height: 1.1;
        text-decoration: none;
    }

    .chip img {
        width: 30px;
        height: 30px;
        border-radius: 50%;
        border: 0.25px solid var(--g999);
    }

    @media (hover: hover) {
        .chip:hover { background-color: var(--navy050); color: var(--accentInk); }
    }

    .chip:focus-visible {
        outline: 2px solid var(--blueOne);
        outline-offset: 2px;
    }
</style>

<nav aria-label="Jump to a team">
    <ul class="chips">
        {#each teams as team}
            <li>
                <a class="chip" href="#team-{team.id}">
                    <img src={team.avatar} alt="" />
                    {team.name}
                </a>
            </li>
        {/each}
    </ul>
</nav>
