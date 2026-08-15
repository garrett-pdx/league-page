<script>
    import { Card, SectionHeading } from '$lib/Design';
    import { getAvatarFromTeamManagers, getTeamFromTeamManagers } from '$lib/utils/helperFunctions/universalFunctions';
    import { managers } from '$lib/utils/leagueInfo';

    /*
    A plaque per championship, newest first, sitting above the illustrated podiums.

    It reads the static dataset rather than getAwards() because it wants each champion's
    SEASON alongside the title -- record and points for -- and the live awards helper returns
    only roster IDs off the bracket, no season figures.

    The join is the fiddly part: final_standings keys on user_id (stable across years) while
    every display helper keys on roster_id (only meaningful within one season). The bridge is
    records[year].roster_id, which is why the roster ID is looked up per year and never reused
    across them.
    */
    let { leagueHistory = null, leagueTeamManagers } = $props();

    const champions = $derived.by(() => {
        if(!leagueHistory?.final_standings) return [];

        return Object.entries(leagueHistory.final_standings)
            .map(([year, table]) => {
                const winner = table.find((r) => r.place === 1);
                if(!winner) return null;

                const manager = leagueHistory.managers?.[winner.user_id];
                const season = manager?.records?.[year];
                if(!season) return null;

                const rosterID = season.roster_id;
                const team = getTeamFromTeamManagers(leagueTeamManagers, rosterID, year);

                /*
                /manager takes an INDEX into leagueInfo's managers array, not a user_id and
                not a roster_id. Resolving it here means each plaque is a real <a href> --
                middle-clickable, and working before hydration -- rather than a div that
                needs JavaScript to go anywhere. -1 when a champion predates the managers
                list, in which case the plaque simply is not a link.
                */
                const managerIndex = managers.findIndex((m) => m.managerID === winner.user_id);

                return {
                    year,
                    rosterID,
                    managerIndex,
                    teamName: team?.name,
                    avatar: getAvatarFromTeamManagers(leagueTeamManagers, rosterID, year),
                    record: season.ties ? `${season.wins}-${season.losses}-${season.ties}` : `${season.wins}-${season.losses}`,
                    pointsFor: season.points_for,
                };
            })
            .filter(Boolean)
            .sort((a, b) => Number(b.year) - Number(a.year));
    });

</script>

<style>
    .plaques {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 1em;
        margin: 0 auto 4em;
        width: 95%;
        max-width: 1000px;
    }

    .plaque {
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        gap: 0.35em;
    }

    .year {
        font-family: var(--fontDisplay);
        font-size: 1.9em;
        font-weight: 700;
        line-height: 1;
        letter-spacing: 0.02em;
        color: var(--navy700);
        font-variant-numeric: tabular-nums;
    }

    .avatar {
        width: 62px;
        height: 62px;
        border-radius: var(--radiusCircle);
        border: 3px solid var(--goldFill);
        background-color: var(--fff);
        margin: 0.25em 0;
    }

    .team {
        font-family: var(--fontDisplay);
        font-size: 1em;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        line-height: 1.15;
        color: var(--navy700);
    }

    .season {
        font-family: var(--fontMono);
        font-size: 0.78em;
        color: var(--g555);
        font-variant-numeric: tabular-nums;
    }

    .empty {
        text-align: center;
        color: var(--g555);
        margin: 2em auto 4em;
    }
</style>

{#if champions.length}
    <SectionHeading eyebrow="The Mudd League" accent="gold">Hall of Fame</SectionHeading>

    <div class="plaques">
        {#each champions as champ (champ.year)}
            <Card
                elevation={champ.managerIndex > -1 ? 'interactive' : 'raised'}
                accent="gold"
                padding="md"
                href={champ.managerIndex > -1 ? `/manager?manager=${champ.managerIndex}` : null}
            >
                <div class="plaque">
                    <span class="year">{champ.year}</span>
                    <img class="avatar" src={champ.avatar} alt="{champ.teamName} avatar" />
                    <span class="team">{champ.teamName}</span>
                    <span class="season">{champ.record} &middot; {champ.pointsFor.toFixed(1)} PF</span>
                </div>
            </Card>
        {/each}
    </div>
{:else if leagueHistory}
    <p class="empty">No championships on record yet.</p>
{/if}
