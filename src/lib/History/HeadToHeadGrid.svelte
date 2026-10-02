<script>
    import { goto } from '$app/navigation';
    import { SectionHeading, SegmentedControl } from '$lib/Design';
    import { headToHead } from '$lib/utils/helper';
    import { managers } from '$lib/utils/leagueInfo';
    import { getTeamData } from '$lib/utils/helperFunctions/universalFunctions';

    /*
    Every manager's record against every other, from games.json (the same rows Schedule luck and
    the Seasons pages use, through headToHead() in leagueGames.js). Mounted at the top of
    routes/rivalry/+page.svelte, above the upstream Rivalry component.

        <HeadToHeadGrid {gamesData} {leagueTeamManagersData} />

    gamesData              getLeagueGames() -- passed as the unawaited promise, like every page
                           in this app, so the heading renders straight away
    leagueTeamManagersData getLeagueTeamManagers() -- only used to tell a Moratorium manager from
                           an active one, and as the fallback for anyone leagueInfo's `managers`
                           doesn't list (their Sleeper handle and avatar)

    TWO LAYOUTS, one data model. At 960px and up it is the full grid. Below that a 12-column
    table does not fit (the narrowest column has to hold "Moratorium"), so it becomes a manager
    picker and that manager's opponents as a list. Both are in the DOM and CSS picks one; the
    hidden one is display:none, so Tab and screen readers only ever meet one set of links.

    COLOUR IS NEVER THE ONLY SIGNAL. Every cell prints its record. The shade only says how lopsided
    it is: blue where the row manager leads, grey where he trails, white when dead even. The
    shades are capped light so navy text on them stays far above 4.5:1.

    Each cell is a real <a href> to /rivalry?player_one=<row>&player_two=<col>, so it can be opened
    in a new tab and reached with Tab. Both parameters are Sleeper user_ids, which is what
    routes/rivalry/+page.js reads. A plain click is handled here instead of by the router, to scroll
    past this grid to the comparison: a #hash on the link does not survive the Rivalry component's
    own goto(), which rewrites the URL the moment its props change.
    */
    export let gamesData;
    export let leagueTeamManagersData = null;

    // In the 2022 league's user list but never held a roster; games.json already omits it, but
    // the dropdowns below do not, so keep the one definition of "not a manager" visible.
    const NEVER_HELD_A_ROSTER = ['612343067143389184'];

    const VIEWS = [
        { value: 'regular', label: 'Regular season' },
        { value: 'playoffs', label: 'Playoffs' },
        { value: 'all', label: 'All games' },
    ];
    // 'all' is no filter at all, so it includes consolation games too.
    const KINDS = { regular: ['regular'], playoffs: ['playoff', 'placement'], all: undefined };
    const VIEW_NOTE = {
        regular: 'Regular season only',
        playoffs: 'Winners bracket and placement games',
        all: 'Every game on record, consolation included',
    };

    let view = 'regular';
    let games = null;
    let ltm = null;
    let loadError = false;

    Promise.all([gamesData, leagueTeamManagersData])
        .then(([g, l]) => { games = g; ltm = l; })
        .catch((err) => { console.error(err); loadError = true; });

    const firstName = (name) => name.split(' ')[0];

    const buildPeople = (data, teamManagers) => {
        const latest = data.through?.season;
        const playedLatest = new Set(data.games.filter((g) => g.season === latest).map((g) => g.user_id));
        const onCurrentRoster = (id) => {
            const rosters = teamManagers?.teamManagersMap?.[teamManagers.currentSeason];
            if(!rosters) return playedLatest.has(id);
            return Object.values(rosters).some((r) => r?.managers?.includes(id));
        };

        return data.managers
            .filter((id) => !NEVER_HELD_A_ROSTER.includes(id))
            .map((id) => {
                const configured = managers.find((m) => m.managerID == id);
                const user = teamManagers?.users?.[id];
                const name = configured?.name ?? user?.user_name ?? user?.display_name ?? 'Unknown';
                return {
                    id,
                    name,
                    first: firstName(name),
                    photo: configured?.photo ?? (user ? getTeamData(teamManagers.users, id).avatar : null),
                    active: onCurrentRoster(id),
                };
            })
            // Alphabetical, so a manager is easy to find in a row of eleven; the Moratorium goes last.
            .sort((a, b) => (b.active - a.active) || a.name.localeCompare(b.name));
    };

    $: people = games ? buildPeople(games, ltm) : [];
    $: h2h = games ? headToHead(games.games, { kinds: KINDS[view] }) : {};

    $: total = Object.fromEntries(people.map((p) => {
        const t = { games: 0, wins: 0, losses: 0, ties: 0 };
        for(const r of Object.values(h2h[p.id] || {})) {
            t.games += r.games; t.wins += r.wins; t.losses += r.losses; t.ties += r.ties;
        }
        return [p.id, t];
    }));

    const record = (r) => r.ties ? `${r.wins}-${r.losses}-${r.ties}` : `${r.wins}-${r.losses}`;
    // A tie is half a win, as everywhere else in the league's numbers.
    const share = (r) => r.games ? (r.wins + r.ties / 2) / r.games : null;
    const percent = (r) => r.games ? `${Math.round(share(r) * 100)}%` : '';
    const winPct = (r) => r.games ? (share(r) * 100).toFixed(1) + '%' : '';

    /*
    Navy for a winning record, grey for a losing one, nothing at .500. The alpha tops out at 0.42:
    navy900 text then measures about 7.6:1 on the strongest blue and about 8.5:1 on the strongest
    grey. The ink is the record itself, so a reader who cannot see the shade still has the answer.
    */
    const shade = (r) => {
        const s = share(r);
        if(s === null) return '';
        const strength = Math.min(Math.abs(s - 0.5) * 2, 1) * 0.42;
        if(strength < 0.02) return '';
        return s > 0.5
            ? `background-color: rgba(0, 74, 143, ${strength.toFixed(3)});`
            : `background-color: rgba(85, 85, 85, ${strength.toFixed(3)});`;
    };

    const href = (a, b) => `/rivalry?player_one=${a}&player_two=${b}`;

    const open = async (e) => {
        // Leave new-tab and download clicks to the browser.
        if(e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
        e.preventDefault();
        await goto(e.currentTarget.getAttribute('href'), { noScroll: true, keepFocus: true });
        const still = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        document.getElementById('compare')?.scrollIntoView({ behavior: still ? 'auto' : 'smooth', block: 'start' });
    };

    // The phone list: one manager's opponents, best record first.
    let pickedId = null;
    $: if(people.length && !people.some((p) => p.id === pickedId)) pickedId = people[0].id;
    $: picked = people.find((p) => p.id === pickedId);
    $: opponents = picked
        ? people
            .filter((p) => p.id !== picked.id && h2h[picked.id]?.[p.id])
            .map((p) => ({ person: p, rec: h2h[picked.id][p.id] }))
            .sort((a, b) => (share(b.rec) - share(a.rec)) || (b.rec.games - a.rec.games) || a.person.name.localeCompare(b.person.name))
        : [];
</script>

<style>
    .note {
        text-align: center;
        color: var(--g555);
        margin: 0 auto 1.4em;
        max-width: 36em;
        width: 90%;
        line-height: 1.45em;
    }

    .onPhone { display: none; }

    .controls {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.7em;
        margin: 0 auto 1.4em;
        width: 94%;
    }

    .stamp {
        margin: 0;
        font-size: 0.875rem;
        color: var(--g555);
        text-align: center;
    }

    .loading, .errorMessage {
        text-align: center;
        color: var(--g555);
        margin: 0 auto;
        width: 90%;
        /* Roughly the height of what replaces it, so the Rivalry controls below don't jump. */
        min-height: 420px;
    }

    .srOnly {
        position: absolute;
        width: 1px;
        height: 1px;
        overflow: hidden;
        clip: rect(0 0 0 0);
        white-space: nowrap;
    }

    /* ---- The grid ------------------------------------------------------------------------ */

    .gridCard {
        width: 94%;
        max-width: var(--pageMax);
        margin: 0 auto;
        background-color: var(--fff);
        border-radius: var(--radiusMd);
        box-shadow: var(--shadowCard);
        padding: 0.6rem 0.5rem 0.9rem;
        box-sizing: border-box;
    }

    table {
        width: 100%;
        table-layout: fixed;
        border-collapse: separate;
        border-spacing: 3px;
    }

    th, td {
        padding: 0;
        font-weight: inherit;
    }

    .corner { width: 150px; }
    .totalCol { width: 84px; }

    .colHead {
        vertical-align: bottom;
        padding-bottom: 0.3rem;
        font-family: var(--fontDisplay);
        font-weight: 500;
        font-size: 0.8125rem;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        color: var(--navy700);
        text-align: center;
        line-height: 1.15;
    }

    .colHead img {
        display: block;
        width: 32px;
        height: 32px;
        object-fit: cover;
        border-radius: var(--radiusCircle);
        margin: 0 auto 0.3rem;
        background-color: var(--fff);
    }

    .tag {
        display: block;
        font-family: var(--fontBody);
        font-size: 0.75rem;
        font-style: italic;
        text-transform: none;
        letter-spacing: 0;
        color: var(--g555);
    }

    .rowHead {
        text-align: left;
        padding-right: 0.5rem;
    }

    .who {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        min-width: 0;
        font-family: var(--fontDisplay);
        font-weight: 500;
        font-size: 0.9375rem;
        text-transform: uppercase;
        letter-spacing: 0.02em;
        color: var(--navy700);
        line-height: 1.1;
    }

    .who img {
        width: 34px;
        height: 34px;
        object-fit: cover;
        flex-shrink: 0;
        border-radius: var(--radiusCircle);
    }

    .cell { height: 50px; }

    .cellLink {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100%;
        min-height: 44px;
        box-sizing: border-box;
        border-radius: var(--radiusSm);
        border: 1px solid var(--accentBorder);
        color: var(--navy900);
        text-decoration: none;
        font-family: var(--fontMono);
        font-variant-numeric: tabular-nums;
        font-size: 0.875rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        white-space: nowrap;
    }

    @media (hover: hover) {
        .cellLink:hover {
            border-color: var(--navy700);
            box-shadow: inset 0 0 0 1px var(--navy700);
        }
    }

    .cellLink:focus-visible {
        outline: 2px solid var(--blueOne);
        outline-offset: 1px;
    }

    .self {
        background-color: var(--navy050);
        border-radius: var(--radiusSm);
    }

    .none {
        text-align: center;
        color: var(--g555);
        font-size: 0.875rem;
    }

    .total {
        text-align: center;
        font-family: var(--fontMono);
        font-variant-numeric: tabular-nums;
        font-weight: 700;
        font-size: 0.875rem;
        color: var(--navy900);
        line-height: 1.25;
        border-left: 2px solid var(--accentBorder);
    }

    .total small {
        display: block;
        font-weight: 400;
        font-size: 0.75rem;
        color: var(--g555);
    }

    /* The Moratorium: a quieter stripe through its row and column, and the label says why. */
    tr.gone .rowHead, th.gone { font-style: italic; }
    tr.gone td:not(.self), td.gone:not(.self) { background-color: var(--navy050); border-radius: var(--radiusSm); }

    .key {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        align-items: center;
        gap: 0.4rem 1.1rem;
        margin: 0.8rem 0 0;
        padding: 0 0.5rem;
        font-size: 0.875rem;
        color: var(--g555);
    }

    .key span { display: inline-flex; align-items: center; gap: 0.4rem; }

    .swatch {
        display: inline-block;
        width: 1.4rem;
        height: 0.9rem;
        border-radius: var(--radiusXs);
        border: 1px solid var(--accentBorder);
    }

    /* ---- The phone list ------------------------------------------------------------------- */

    .picker {
        width: 94%;
        max-width: 520px;
        margin: 0 auto 1rem;
    }

    .picker label {
        display: block;
        font-family: var(--fontDisplay);
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: var(--g555);
        margin: 0 0 0.35rem 0.2rem;
    }

    .picker select {
        display: block;
        width: 100%;
        min-height: 48px;
        box-sizing: border-box;
        padding: 0.4em 2.4em 0.4em 0.9em;
        font-size: 1.05rem;
        color: var(--g000);
        background-color: var(--fff);
        border: 1px solid var(--accentBorder);
        border-radius: var(--radiusSm);
        appearance: none;
        -webkit-appearance: none;
        background-image: url(/dropdown.png);
        background-repeat: no-repeat;
        background-position: 100%;
    }

    .picker select:focus-visible {
        outline: 2px solid var(--blueOne);
        outline-offset: 1px;
    }

    .summary {
        width: 94%;
        max-width: 520px;
        margin: 0 auto 0.6rem;
        text-align: center;
        color: var(--g555);
        font-size: 0.9375rem;
    }

    .summary strong {
        font-family: var(--fontMono);
        color: var(--navy900);
    }

    .opps {
        list-style: none;
        margin: 0 auto;
        padding: 0;
        width: 94%;
        max-width: 520px;
        background-color: var(--fff);
        border-radius: var(--radiusMd);
        box-shadow: var(--shadowCard);
        overflow: hidden;
    }

    .opp {
        display: grid;
        grid-template-columns: 36px minmax(0, 1fr) auto;
        align-items: center;
        gap: 0.2rem 0.7rem;
        min-height: 44px;
        padding: 0.6rem 0.8rem;
        border-bottom: 1px solid var(--accentBorder);
        color: inherit;
        text-decoration: none;
    }

    .opps li:last-child .opp { border-bottom: none; }

    .opp:focus-visible {
        outline: 2px solid var(--blueOne);
        outline-offset: -2px;
    }

    .opp img {
        width: 36px;
        height: 36px;
        object-fit: cover;
        border-radius: var(--radiusCircle);
        grid-row: 1 / span 2;
    }

    .oppName {
        font-family: var(--fontDisplay);
        font-weight: 500;
        font-size: 1rem;
        text-transform: uppercase;
        letter-spacing: 0.02em;
        color: var(--navy700);
        line-height: 1.1;
    }

    .oppRec {
        font-family: var(--fontMono);
        font-variant-numeric: tabular-nums;
        font-weight: 700;
        color: var(--navy900);
        text-align: right;
    }

    .share {
        grid-column: 2 / span 2;
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }

    .track {
        position: relative;
        flex: 1;
        height: 0.6rem;
        border-radius: var(--radiusPill);
        background-color: var(--navy100);
        overflow: hidden;
    }

    .fill {
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        background-color: var(--accentFill);
    }

    .track::after {
        content: '';
        position: absolute;
        left: 50%;
        top: 0;
        bottom: 0;
        width: 2px;
        background-color: var(--fff);
    }

    .pct {
        flex: 0 0 2.6rem;
        text-align: right;
        font-family: var(--fontMono);
        font-size: 0.8125rem;
        color: var(--g555);
    }

    .empty {
        text-align: center;
        color: var(--g555);
        padding: 1.2rem 1rem;
    }

    @media (max-width: 959px) {
        .onDesktop { display: none; }
        .onPhone { display: block; }
        .loading, .errorMessage { min-height: 300px; }
    }
</style>

<SectionHeading level={3}>Head to head</SectionHeading>

<p class="note">
    <span class="onDesktop">Everyone's record against everyone else since 2022, kept by someone who was paying attention. Tap a cell for the full rivalry.</span>
    <span class="onPhone">Everyone's record against everyone else since 2022, kept by someone who was paying attention. Pick a manager, then tap an opponent for the full rivalry.</span>
</p>

{#if loadError}
    <p class="errorMessage">The head-to-head records could not be loaded. Try refreshing the page.</p>
{:else if !games}
    <p class="loading">Pulling the old box scores...</p>
{:else}
    <div class="controls">
        <SegmentedControl options={VIEWS} bind:value={view} ariaLabel="Which games to count" />
        <p class="stamp">
            {VIEW_NOTE[view]}. Through {games.through.season} week {games.through.week}.
        </p>
    </div>

    <!-- Desktop: the grid -->
    <div class="onDesktop gridCard">
        <table>
            <caption class="srOnly">
                Head-to-head records. Each cell is the row manager's record against the column manager,
                and links to their full rivalry.
            </caption>
            <thead>
                <tr>
                    <td class="corner"></td>
                    {#each people as col}
                        <th scope="col" class="colHead" class:gone={!col.active}>
                            {#if col.photo}<img src={col.photo} alt="" />{/if}
                            {col.first}
                            {#if !col.active}<span class="tag">Moratorium</span>{/if}
                        </th>
                    {/each}
                    <th scope="col" class="colHead totalCol">Total</th>
                </tr>
            </thead>
            <tbody>
                {#each people as row}
                    <tr class:gone={!row.active}>
                        <th scope="row" class="rowHead">
                            <span class="who">
                                {#if row.photo}<img src={row.photo} alt="" />{/if}
                                <span>
                                    {row.name}
                                    {#if !row.active}<span class="tag">Moratorium</span>{/if}
                                </span>
                            </span>
                        </th>
                        {#each people as col}
                            {@const rec = h2h[row.id]?.[col.id]}
                            {#if row.id === col.id}
                                <td class="cell self"></td>
                            {:else if rec}
                                <td class="cell">
                                    <a
                                        class="cellLink"
                                        href={href(row.id, col.id)}
                                        style={shade(rec)}
                                        on:click={open}
                                        aria-label="{row.name} against {col.name}: {record(rec)}. Open the rivalry."
                                    >{record(rec)}</a>
                                </td>
                            {:else}
                                <td class="cell none" class:gone={!col.active}><span aria-hidden="true">–</span><span class="srOnly">{row.name} and {col.name} never met</span></td>
                            {/if}
                        {/each}
                        <td class="cell total">
                            {record(total[row.id])}
                            <small>{winPct(total[row.id])}</small>
                        </td>
                    </tr>
                {/each}
            </tbody>
        </table>
        <div class="key" aria-hidden="true">
            <span><i class="swatch" style="background-color: rgba(0, 74, 143, 0.42);"></i>Row manager leads</span>
            <span><i class="swatch"></i>Dead even</span>
            <span><i class="swatch" style="background-color: rgba(85, 85, 85, 0.42);"></i>Row manager trails</span>
            <span>– never met</span>
        </div>
    </div>

    <!-- Phones: pick a manager, read down their opponents -->
    <div class="onPhone">
        <div class="picker">
            <label for="h2hManager">Manager</label>
            <select id="h2hManager" bind:value={pickedId}>
                {#each people as p}
                    <option value={p.id}>{p.name}{p.active ? '' : ' (Moratorium)'}</option>
                {/each}
            </select>
        </div>

        {#if picked}
            <p class="summary">
                {picked.first} overall: <strong>{record(total[picked.id])}</strong>
                {#if total[picked.id].games}({winPct(total[picked.id])}){/if}
            </p>

            {#if opponents.length}
                <ul class="opps">
                    {#each opponents as { person, rec } (person.id)}
                        <li>
                            <a class="opp" href={href(picked.id, person.id)} on:click={open}>
                                {#if person.photo}<img src={person.photo} alt="" />{:else}<span></span>{/if}
                                <span class="oppName">{person.name}{person.active ? '' : ' (Moratorium)'}</span>
                                <span class="oppRec">{record(rec)}</span>
                                <span class="share">
                                    <span class="track" aria-hidden="true"><span class="fill" style="width: {share(rec) * 100}%;"></span></span>
                                    <span class="pct">{percent(rec)}</span>
                                </span>
                            </a>
                        </li>
                    {/each}
                </ul>
            {:else}
                <p class="empty">No games on record for {picked.first} in this view.</p>
            {/if}
        {/if}
    </div>
{/if}
