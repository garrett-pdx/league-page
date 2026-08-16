<script>
    import { SectionHeading } from '$lib/Design';
    import { getTeamFromTeamManagers, getAvatarFromTeamManagers } from '$lib/utils/helperFunctions/universalFunctions';
    import { managers } from '$lib/utils/leagueInfo';

    /*
    Shown on /standings while the current season has no games. Standings is a top-level nav item
    and for roughly seven months of the year it said "Preseason, No Standings Yet" and nothing
    else -- a whole page of blank on a link people actually click.

    This needs no new data. final_standings is the only source for a full 1-10 placement (Sleeper
    exposes the podium and the toilet bowl and nothing between), and it is already fetched and
    memoised by helperFunctions/leagueHistory.js for the manager career band and the Hall of Fame.

    The join is the usual one: final_standings keys on user_id, every display helper keys on
    roster_id, and records[season].roster_id bridges them per season. Never reuse a roster ID
    across years.
    */
    // Both props go through $props(): Svelte 5 does not allow `export let` alongside it.
    let { leagueHistory = null, leagueTeamManagers } = $props();

    const season = $derived.by(() => {
        const seasons = Object.keys(leagueHistory?.final_standings || {});
        return seasons.length ? seasons.sort().pop() : null;
    });

    const rows = $derived.by(() => {
        if(!season) return [];
        return (leagueHistory.final_standings[season] || [])
            .map((entry) => {
                const manager = leagueHistory.managers?.[entry.user_id];
                const record = manager?.records?.[season];
                if(!record) return null;
                const rosterID = record.roster_id;
                return {
                    place: entry.place,
                    rosterID,
                    team: getTeamFromTeamManagers(leagueTeamManagers, rosterID, season)?.name,
                    avatar: getAvatarFromTeamManagers(leagueTeamManagers, rosterID, season),
                    record: record.ties ? `${record.wins}-${record.losses}-${record.ties}` : `${record.wins}-${record.losses}`,
                    pointsFor: record.points_for,
                    managerIndex: managers.findIndex((m) => m.managerID === entry.user_id),
                };
            })
            .filter(Boolean)
            .sort((a, b) => a.place - b.place);
    });
</script>

<style>
    .intro {
        text-align: center;
        color: var(--g555);
        margin: 0 auto 2em;
        max-width: 34em;
        width: 92%;
    }

    .table {
        width: 94%;
        max-width: 640px;
        margin: 0 auto 5em;
        background-color: var(--fff);
        border-radius: var(--radiusMd);
        box-shadow: var(--shadowCard);
        overflow: hidden;
    }

    .row {
        display: grid;
        grid-template-columns: 2.6em 1fr 4.5em 5em;
        align-items: center;
        gap: 0.5em;
        padding: 0.6em 0.9em;
        border-bottom: 1px solid var(--accentBorder);
        color: inherit;
        text-decoration: none;
    }

    .row:last-child { border-bottom: none; }

    @media (hover: hover) {
        a.row:hover { background-color: var(--navy050); }
    }

    a.row:focus-visible {
        outline: 2px solid var(--blueOne);
        outline-offset: -2px;
    }

    .head {
        font-family: var(--fontDisplay);
        font-size: 0.72em;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--g555);
        background-color: var(--navy050);
    }

    .place {
        font-family: var(--fontMono);
        font-weight: 700;
        color: var(--navy700);
        font-variant-numeric: tabular-nums;
    }

    /* Gold is a fill and never ink, so the champion is a filled chip rather than gold text. */
    .champion .place {
        background-color: var(--goldFill);
        color: var(--goldOnFill);
        border-radius: var(--radiusPill);
        text-align: center;
        padding: 0.15em 0;
    }

    .team {
        display: flex;
        align-items: center;
        gap: 0.5em;
        min-width: 0;
    }

    .team span {
        font-family: var(--fontDisplay);
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.02em;
        line-height: 1.15;
        overflow-wrap: anywhere;
    }

    .avatar {
        width: 28px;
        height: 28px;
        border-radius: var(--radiusCircle);
        flex-shrink: 0;
        background-color: var(--fff);
    }

    .num {
        font-family: var(--fontMono);
        font-variant-numeric: tabular-nums;
        text-align: right;
        color: var(--g555);
        font-size: 0.9em;
    }

    @media (max-width: 430px) {
        .row { grid-template-columns: 2.2em 1fr 4em; padding: 0.55em 0.6em; }
        .pf { display: none; }
        .avatar { width: 24px; height: 24px; }
    }
</style>

{#if rows.length}
    <SectionHeading eyebrow="Last completed season" accent="gold">{season} Final Standings</SectionHeading>

    <p class="intro">The {season} season is in the books. Here is how it finished while we wait for
    week one.</p>

    <div class="table">
        <div class="row head">
            <span>#</span>
            <span>Team</span>
            <span class="num">Record</span>
            <span class="num pf">Points</span>
        </div>
        {#each rows as row (row.place)}
            <svelte:element
                this={row.managerIndex > -1 ? 'a' : 'div'}
                href={row.managerIndex > -1 ? `/manager?manager=${row.managerIndex}` : undefined}
                class="row"
                class:champion={row.place === 1}
            >
                <span class="place">{row.place}</span>
                <span class="team">
                    <img class="avatar" src={row.avatar} alt="" />
                    <span>{row.team}</span>
                </span>
                <span class="num">{row.record}</span>
                <span class="num pf">{row.pointsFor.toFixed(1)}</span>
            </svelte:element>
        {/each}
    </div>
{/if}
