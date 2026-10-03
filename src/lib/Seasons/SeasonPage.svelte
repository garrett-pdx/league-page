<script>
    /*
    One Sleeper season's page (2022 onwards), top to bottom: champion, final table and all-play,
    playoff bracket, standings by week, draft and keepers, trades, extremes.

    A season still being played (no final_standings yet) gets "in progress": standings so far
    from games.json, links to the live Standings and Matchups pages, and no final table, bracket
    or champion. games.json only holds completed weeks, so "so far" is "through week N".

    Everything except the all-play table renders from the static dataset. The all-play table
    names teams through the Sleeper roster walk (getLeagueTeamManagers), so it waits on that
    alone.
    */
    import { waitForAll, filterGames, allPlay, lineupTotals } from '$lib/utils/helper';
    import { managers } from '$lib/utils/leagueInfo';
    import { SectionHeading } from '$lib/Design';
    import AllPlayTable from '$lib/History/AllPlayTable.svelte';
    import FinalTable from './FinalTable.svelte';
    import Bracket from './Bracket.svelte';
    import RankChart from './RankChart.svelte';
    import DraftRounds from './DraftRounds.svelte';
    import Keepers from './Keepers.svelte';
    import Trades from './Trades.svelte';
    import Extremes from './Extremes.svelte';
    import {
        peopleLookup, isComplete, finalTable, regularStandings, seasonBracket, ranksByWeek,
        seasonExtremes, seasonMvps, seasonDraft, earlyRounds, seasonKeepers, titleGame,
    } from './seasonData';

    export let year;
    export let history;
    export let gamesData, notesData, keepersData, playersData, leagueTeamManagersData;

    const people = peopleLookup(history, managers);
    const complete = isComplete(history, year);
    const draft = seasonDraft(history, year);
    const teams = history.seasons?.[String(year)]?.teams || 10;

    const sections = [
        ['standings', complete ? 'Final table' : 'Standings'],
        ...(complete ? [['bracket', 'Bracket']] : []),
        ['by-week', 'By week'],
        ['draft', 'Draft'],
        ['trades', 'Trades'],
        ['extremes', 'Extremes'],
    ];

    const pts = (n) => n.toFixed(2);
</script>

<style>
    .jump {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 0.4rem;
        width: 94%;
        max-width: var(--pageMax);
        margin: 0 auto 1.5rem;
        padding: 0;
        list-style: none;
    }

    .jump a, .live a, .more a {
        display: inline-flex;
        align-items: center;
        min-height: 44px;
        padding: 0 1em;
        box-sizing: border-box;
        border: 1px solid var(--accentBorder);
        border-radius: var(--radiusPill);
        background-color: var(--fff);
        color: var(--navy700);
        font-size: 0.9rem;
        text-decoration: none;
    }

    @media (hover: hover) {
        .jump a:hover, .live a:hover, .more a:hover { background-color: var(--navy050); color: var(--accentInk); }
    }

    .jump a:focus-visible, .live a:focus-visible, .more a:focus-visible {
        outline: 2px solid var(--blueOne);
        outline-offset: 2px;
    }

    section {
        scroll-margin-top: calc(var(--stickyBar, 0px) + 8px);
    }

    /* ---- the champion ---- */
    .hero {
        width: 94%;
        max-width: 560px;
        margin: 0 auto 1.5rem;
        text-align: center;
    }

    .ribbonWrap {
        position: relative;
        width: 80%;
        max-width: 400px;
        margin: 0 auto;
    }

    .ribbon { display: block; width: 100%; height: auto; aspect-ratio: 450 / 110; }

    .ribbonText {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        font-family: var(--fontDisplay);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--goldOnFill);
        font-size: clamp(0.9rem, 4vw, 1.4rem);
        line-height: 1;
        white-space: nowrap;
        pointer-events: none;
    }

    .champPhoto {
        display: block;
        width: 112px;
        height: 112px;
        margin: 0.9rem auto 0.4rem;
        border-radius: var(--radiusCircle);
        object-fit: cover;
        border: 4px solid var(--goldFill);
        box-shadow: var(--shadowCard);
    }

    .champName {
        font-family: var(--fontDisplay);
        font-size: 1.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.02em;
        line-height: 1.1;
        margin: 0;
    }

    .champName a {
        display: inline-flex;
        align-items: center;
        min-height: 44px;
        color: var(--navy700);
        text-decoration: none;
    }

    @media (hover: hover) {
        .champName a:hover { text-decoration: underline; }
    }

    .final {
        margin: 0.2rem 0 0;
        color: var(--g444);
        line-height: 1.45;
    }

    .num { font-variant-numeric: tabular-nums; white-space: nowrap; }

    /* ---- in progress ---- */
    .live {
        width: 94%;
        max-width: 640px;
        margin: 0 auto 1.5rem;
        padding: 1rem 1.1rem;
        background-color: var(--fff);
        border-radius: var(--radiusMd);
        box-shadow: var(--shadowCard);
        border-top: 3px solid var(--accentFill);
        text-align: center;
        color: var(--g444);
        line-height: 1.45;
        box-sizing: border-box;
    }

    .live p { margin: 0 0 0.8rem; }

    .links {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 0.5rem;
    }

    .note {
        text-align: center;
        color: var(--g555);
        margin: 0 auto 1.2em;
        max-width: 36em;
        width: 92%;
        line-height: 1.45;
    }

    .more {
        display: flex;
        justify-content: center;
        margin: 0 auto 1.5em;
    }

    .loading {
        min-height: 120vh;
        text-align: center;
        color: var(--g555);
    }

    .warn {
        text-align: center;
        color: #a32020;
        margin: 0 auto 1em;
    }
</style>

<nav aria-label="Sections of this season">
    <ul class="jump">
        {#each sections as [id, label]}
            <li><a href="#{id}">{label}</a></li>
        {/each}
    </ul>
</nav>

{#await waitForAll(gamesData, notesData, keepersData, playersData)}
    <p class="loading">Opening the {year} file...</p>
{:then [{games}, notes, keepersFile, players]}
    {@const table = complete ? finalTable(history, games, year) : regularStandings(games, year)}
    {@const through = notes.seasons?.[String(year)]?.through_week}
    {@const order = table.map((r) => r.user_id)}
    {@const regular = filterGames(games, {seasons: [year], kinds: ['regular']})}
    {@const keepers = seasonKeepers(history, keepersFile, year)}

    {#if complete}
        {@const champ = table[0]?.user_id}
        {@const tg = titleGame(history, games, year)}
        <div class="hero">
            <div class="ribbonWrap">
                <img class="ribbon" src="/brand/banner.svg" alt="" width="450" height="110" />
                <span class="ribbonText">{year} Champion</span>
            </div>
            {#if people[champ]?.photo}
                <img class="champPhoto" src={people[champ].photo} alt="" width="112" height="112" />
            {/if}
            <p class="champName">
                {#if people[champ]?.href}<a href={people[champ].href}>{people[champ].name}</a>{:else}{people[champ]?.name}{/if}
            </p>
            {#if tg}
                <p class="final">
                    Beat {people[tg.opponent_id]?.name} <span class="num">{pts(tg.pf)}–{pts(tg.pa)}</span> in the
                    week {tg.week} final, as the {table[0].seed}-seed.
                </p>
            {/if}
        </div>
    {:else}
        <div class="live">
            <p><strong>In progress.</strong> {through ? `These are the standings through week ${through}, the last week fully played when the archive was updated.` : 'No week has been completed yet.'} The live table and this week's games are on their own pages.</p>
            <div class="links">
                <a href="/standings">Live standings</a>
                <a href="/matchups">This week's matchups</a>
            </div>
        </div>
    {/if}

    <section id="standings">
        <SectionHeading level={3} eyebrow={complete ? 'Where everyone finished' : `Through week ${through}`}>
            {complete ? 'Final standings' : 'Standings so far'}
        </SectionHeading>
        {#if complete}
            <p class="note">Places 1–4 are the playoffs, 5–8 the consolation bracket, 9 and 10 the regular season's leftovers. Record and points are the regular season's.</p>
        {/if}
        <FinalTable rows={table} {people} final={complete} />

        {#await leagueTeamManagersData}
            <p class="note">Loading the all-play table...</p>
        {:then leagueTeamManagers}
            <AllPlayTable rows={allPlay(regular)} {leagueTeamManagers} season={year} />
        {:catch}
            <p class="note">The all-play table needs Sleeper, which didn't answer.</p>
        {/await}
    </section>

    {#if complete}
        {@const bracket = seasonBracket(history, games, year)}
        <section id="bracket">
            <SectionHeading level={3} eyebrow="Weeks {history.seasons[String(year)].playoff_week_start}–{history.seasons[String(year)].playoff_week_start + 1}">Playoff bracket</SectionHeading>
            {#if bracket}<Bracket {bracket} {people} />{/if}
        </section>
    {/if}

    <section id="by-week">
        <SectionHeading level={3} eyebrow="Regular season">Standings by week</SectionHeading>
        <p class="note">Each team's place in the table after every week: wins first, then points for.</p>
        <RankChart ranksData={ranksByWeek(games, year)} {people} selected={order[0]} />
    </section>

    <section id="draft">
        <SectionHeading level={3} eyebrow={draft ? `${draft.rounds} rounds` : null}>Draft and keepers</SectionHeading>
        {#if draft}
            <DraftRounds rounds={earlyRounds(draft, 3)} {teams} {players} {people} />
            <SectionHeading level={4} rule={false}>{keepers.rows.length} keepers</SectionHeading>
            {#if !keepers.agrees}
                <p class="warn">The keeper list and the draft's keeper flags disagree for this season.</p>
            {/if}
            <p class="note">A keeper takes the draft slot he costs, so the round is the price.</p>
            <Keepers rows={keepers.rows} {year} {players} {people} />
        {:else}
            <p class="note">No completed draft on record for {year}.</p>
        {/if}
        <div class="more"><a href="/drafts">Every round on the full draft board →</a></div>
    </section>

    <section id="trades">
        <SectionHeading level={3}>Trades</SectionHeading>
        <Trades trades={notes.seasons?.[String(year)]?.trades || []} {people} />
    </section>

    <section id="extremes">
        <SectionHeading level={3} eyebrow={complete ? null : `Through week ${through}`}>Season extremes</SectionHeading>
        <Extremes
            extremes={seasonExtremes(games, notes, year)}
            lineups={lineupTotals(regular)}
            mvps={seasonMvps(notes, year)}
            {order}
            {people}
            partial={!complete}
        />
    </section>
{:catch error}
    <p class="warn">The archive wouldn't open: {error.message}</p>
{/await}
