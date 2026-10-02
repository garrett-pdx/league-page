<script>
    import { SectionHeading } from '$lib/Design';
    import { managers } from '$lib/utils/leagueInfo';

    /*
    The all-play / schedule-luck table. PRESENTATIONAL: it takes the rows allPlay() returns and
    draws them, and fetches nothing. Standings feeds it live rows through ScheduleLuck.svelte;
    a Seasons page feeds it one finished season straight from games.json.

        <AllPlayTable rows={allPlay(filterGames(games, {seasons: [2024], kinds: ['regular']}))}
                      {leagueTeamManagers} season={2024} />

    rows                 allPlay() output (see leagueGames.js for the fields)
    leagueTeamManagers   the resolved getLeagueTeamManagers()
    season               which season's rosters name the teams. Roster IDs mean nothing across
                         seasons, so a team is found by user_id inside THAT year's roster map --
                         the same join LastSeason.svelte does.
    eyebrow              small label over the heading, e.g. "Through week 3"
    heading              pass false when a page supplies its own
    note                 the sentence under the heading; a default is used when omitted

    LUCK IS NEVER COLOUR ALONE. Every value carries its sign, and the bar runs right of the
    centre line for lucky and left for unlucky; the two fills differ in colour too, but a reader
    who can't tell them apart still gets both the "+/-" and the direction.
    */
    export let rows = [];
    export let leagueTeamManagers;
    export let season;
    export let eyebrow = null;
    export let heading = true;
    export let note = null;

    // user_id -> {name, avatar, index}, for this season only
    const teamLookup = (ltm, year) => {
        const out = {};
        const rosters = ltm?.teamManagersMap?.[year] || {};
        for(const rosterID in rosters) {
            const roster = rosters[rosterID];
            if(!roster) continue;
            for(const uid of roster.managers || []) {
                out[uid] = {
                    name: roster.team?.name,
                    avatar: roster.team?.avatar,
                    index: managers.findIndex((m) => m.managerID == uid),
                };
            }
        }
        return out;
    };

    $: teams = teamLookup(leagueTeamManagers, season);
    // The longest bar is the luckiest (or unluckiest) team; everything else scales to it.
    $: maxLuck = Math.max(0.01, ...rows.map((r) => Math.abs(r.luck)));

    const record = (w, l, t) => t ? `${w}-${l}-${t}` : `${w}-${l}`;
    const sign = (n) => {
        const v = Math.round(n * 100) / 100;
        if(v === 0) return '0.00';
        return `${v > 0 ? '+' : '−'}${Math.abs(v).toFixed(2)}`;
    };
    // Half the track is each direction, so the longest bar fills 50%.
    const barWidth = (luck) => `${Math.max(Math.abs(luck) / maxLuck * 50, 3)}%`;
    const describe = (luck) => {
        const v = Math.round(luck * 100) / 100;
        if(v === 0) return 'exactly as many wins as the schedule owed';
        return `${Math.abs(v).toFixed(2)} wins ${v > 0 ? 'more' : 'fewer'} than the schedule owed`;
    };
</script>

<style>
    .note {
        text-align: center;
        color: var(--g555);
        margin: 0 auto 2em;
        max-width: 34em;
        width: 92%;
        line-height: 1.45em;
    }

    .table {
        width: 94%;
        max-width: 760px;
        margin: 0 auto 5em;
        background-color: var(--fff);
        border-radius: var(--radiusMd);
        box-shadow: var(--shadowCard);
        overflow: hidden;
        text-align: left;
    }

    .row {
        display: grid;
        /* rem, not em: the header row is a smaller font than the body rows, and the columns have
           to line up between them. */
        grid-template-columns: minmax(0, 1fr) 5.2rem 4.4rem 3.8rem 9.5rem;
        align-items: center;
        gap: 0.5rem;
        padding: 0.6rem 0.9rem;
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
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--g555);
        background-color: var(--navy050);
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
        overflow-wrap: break-word;
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
        white-space: nowrap;
    }

    .head .num { font-size: inherit; font-family: inherit; }

    /* The luck cell: a track with a centre line, then the signed number. */
    .luck {
        position: relative;
        display: flex;
        align-items: center;
        justify-content: flex-end;
        gap: 0.5em;
    }

    .track {
        position: relative;
        flex: 0 0 3.6em;
        height: 0.8em;
    }

    .track::before {
        content: '';
        position: absolute;
        left: 50%;
        top: -2px;
        bottom: -2px;
        width: 1px;
        background-color: var(--g555);
        opacity: 0.55;
    }

    .bar {
        position: absolute;
        top: 0.15em;
        bottom: 0.15em;
        border-radius: var(--radiusXs);
    }

    .bar.up {
        left: 50%;
        max-width: 50%;
        background-color: var(--accentFill);
    }

    .bar.down {
        right: 50%;
        max-width: 50%;
        background-color: var(--g555);
    }

    .srOnly {
        position: absolute;
        width: 1px;
        height: 1px;
        overflow: hidden;
        clip: rect(0 0 0 0);
        white-space: nowrap;
    }

    .luckNum {
        flex: 0 0 3.4em;
        color: var(--navy700);
        font-weight: 700;
    }

    /* Four columns on a phone: team, all-play record, expected wins, luck. The all-play % is
       the record restated, so it is the one that goes. */
    @media (max-width: 560px) {
        .row {
            grid-template-columns: minmax(0, 1fr) 3.9rem 3rem 5.8rem;
            padding: 0.55rem 0.6rem;
            gap: 0.4rem;
        }
        .pct { display: none; }
        .avatar { width: 24px; height: 24px; }
        .team span { font-size: 0.9em; }
        .track { flex-basis: 2.4em; }
        .luckNum { flex-basis: 3em; }
        .luck { gap: 0.4em; }
    }
</style>

{#if rows.length}
    {#if heading}
        <SectionHeading level={3} {eyebrow}>Schedule luck</SectionHeading>
    {/if}

    <p class="note">
        {#if note}{note}{:else}Every week, each team is also scored against the other nine, not only the one it
        drew. Luck is actual wins minus the wins that record deserved. A minus means the schedule
        has it in for you.{/if}
    </p>

    <div class="table">
        <div class="row head">
            <span>Team</span>
            <span class="num">All-play</span>
            <span class="num pct">Win %</span>
            <span class="num">Exp. W</span>
            <span class="num">Luck</span>
        </div>
        {#each rows as row (row.user_id)}
            {@const team = teams[row.user_id]}
            <svelte:element
                this={team && team.index > -1 ? 'a' : 'div'}
                href={team && team.index > -1 ? `/manager?manager=${team.index}` : undefined}
                class="row"
               
            >
                <span class="team">
                    {#if team?.avatar}<img class="avatar" src={team.avatar} alt="" />{/if}
                    <span>{team?.name ?? 'Unknown team'}</span>
                </span>
                <span class="num">{record(row.allPlayWins, row.allPlayLosses, row.allPlayTies)}</span>
                <span class="num pct">{row.allPlayPct === null ? '' : (row.allPlayPct * 100).toFixed(1) + '%'}</span>
                <span class="num">{row.expectedWins.toFixed(1)}</span>
                <span class="luck">
                    <span class="srOnly">{describe(row.luck)}</span>
                    <span class="track" aria-hidden="true">
                        {#if Math.abs(row.luck) >= 0.005}
                            <span class="bar {row.luck > 0 ? 'up' : 'down'}" style="width: {barWidth(row.luck)};"></span>
                        {/if}
                    </span>
                    <span class="num luckNum" aria-hidden="true">{sign(row.luck)}</span>
                </span>
            </svelte:element>
        {/each}
    </div>
{/if}
