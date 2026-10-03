/*
The Seasons archive's numbers, as pure functions over the committed dataset: league-history.json,
games.json (decoded by getLeagueGames), season-notes.json and keepers.json. No Svelte, no fetch,
no $lib imports, so Node can import and check it directly.

Three traps this file exists to keep in one place:

  * ROSTER IDS MOVE BETWEEN SEASONS. A bracket row carries roster IDs, which mean something only
    inside their own season; they become user_ids through managers[uid].records[season].roster_id
    for THAT season. rosterUsers() is the only place that join happens.
  * 2022 HAS TWO DRAFTS AND ONE OF THEM ISN'T A 2022 DRAFT. The `primary` one is the 2022 draft;
    the other is the league's 2021 (ESPN) draft, re-uploaded into Sleeper and filed under 2022.
    seasonDraft() takes the primary only; carriedOverDraft() is the 2021 page's draft.
  * AN UNPLAYED SEASON LOOKS REAL. final_standings only holds completed seasons, so "is there a
    final table" is the test for "is this season finished" -- never "is there a season entry".
*/

// The league was founded on ESPN in 2021 and moved to Sleeper for 2022. Only the draft survived.
export const FOUNDING_SEASON = 2021;

// The 2021 draft's Sleeper id, for code that sees Sleeper's live draft list rather than the
// dataset (the /drafts page). The dataset marks the same draft with `primary: false`.
export const CARRIED_OVER_DRAFT_ID = '819042961097633792';

const round2 = (n) => Math.round(n * 100) / 100;

/** Every year with a page, newest first: the Sleeper seasons plus the ESPN founding season. */
export const archiveYears = (history) => {
    const years = Object.keys(history.seasons || {}).map(Number);
    years.push(FOUNDING_SEASON);
    return [...new Set(years)].sort((a, b) => b - a);
}

/** True once a season has a final table, i.e. its bracket is complete. */
export const isComplete = (history, year) => Boolean(history.final_standings?.[String(year)]?.length);

/** roster_id -> user_id for one season. */
export const rosterUsers = (history, year) => {
    const out = {};
    for(const [uid, m] of Object.entries(history.managers || {})) {
        const rec = m.records?.[String(year)];
        if(rec && rec.roster_id !== undefined && rec.roster_id !== null) out[rec.roster_id] = uid;
    }
    return out;
}

/**
 * user_id -> display info. `managers` is leagueInfo's array (passed in so this file stays pure);
 * anyone not in it falls back to their Sleeper handle from the dataset.
 */
export const peopleLookup = (history, managers = []) => {
    const out = {};
    for(const [uid, m] of Object.entries(history.managers || {})) {
        const index = managers.findIndex((x) => x.managerID == uid);
        const entry = index > -1 ? managers[index] : null;
        const name = entry?.name || m.handle || 'Unknown';
        out[uid] = {
            user_id: uid,
            name,
            first: name.split(' ')[0],
            handle: m.handle,
            photo: entry?.photo || null,
            href: index > -1 ? `/manager?manager=${index}` : null,
        };
    }
    return out;
}

const gamesOf = (games, year, kinds) => games.filter((g) =>
    g.season === Number(year) && (!kinds || kinds.includes(g.kind)));

/** The row for one bracket game, from t1's side; null when it hasn't been played. */
const findGame = (games, year, week, a, b) =>
    games.find((g) => g.season === Number(year) && g.week === week && g.user_id === a && g.opponent_id === b) || null;

/**
 * The playoff bracket, read-only, from league-history.json `brackets` with scores from games.json.
 *
 *   {winners: [round], losers: [round]}    round = {label, games: [game]}
 *   game = {label, week, a: {user_id, seed, pf, won}, b: {...}, place}
 *
 * Bracket round r is played in week playoff_week_start + r - 1. A game's `p` is the place its
 * winner takes (1 = title, 3 = third; the losers bracket repeats it for 5th and 7th), so the
 * consolation bracket's p is offset by four.
 */
export const seasonBracket = (history, games, year) => {
    const y = String(year);
    const raw = history.brackets?.[y];
    const season = history.seasons?.[y];
    if(!raw || !season) return null;

    const users = rosterUsers(history, y);
    const seeds = {};
    regularStandings(games, year).forEach((r, i) => { seeds[r.user_id] = i + 1; });
    const start = season.playoff_week_start;

    const build = (rows, offset, names) => {
        const byRound = {};
        for(const m of rows || []) {
            const a = users[m.t1], b = users[m.t2];
            if(!a || !b) continue;
            const week = start + m.r - 1;
            const row = findGame(games, y, week, a, b);
            const winner = m.w ? users[m.w] : null;
            const game = {
                week,
                place: m.p ? m.p + offset : null,
                label: m.p ? names.place(m.p + offset) : names.round(m.r),
                a: {user_id: a, seed: seeds[a], pf: row ? row.pf : null, won: winner === a},
                b: {user_id: b, seed: seeds[b], pf: row ? row.pa : null, won: winner === b},
            };
            (byRound[m.r] || (byRound[m.r] = [])).push(game);
        }
        return Object.keys(byRound).map(Number).sort((p, q) => p - q).map((r) => ({
            label: names.roundLabel(r),
            // the title game first, then third place
            games: byRound[r].sort((p, q) => (p.place ?? 0) - (q.place ?? 0)),
        }));
    };

    const placeName = (p) => p === 1 ? 'Championship' : `${ordinalWord(p)} place`;

    return {
        winners: build(raw.winners, 0, {
            round: () => 'Semifinal',
            roundLabel: (r) => r === 1 ? `Semifinals · week ${start}` : `Finals · week ${start + 1}`,
            place: placeName,
        }),
        losers: build(raw.losers, 4, {
            round: () => 'Consolation',
            roundLabel: (r) => r === 1 ? `Consolation · week ${start}` : `Placement games · week ${start + 1}`,
            place: placeName,
        }),
    };
}

const ordinalWord = (n) => {
    const v = n % 100;
    return n + (['th', 'st', 'nd', 'rd'][(v - 20) % 10] || ['th', 'st', 'nd', 'rd'][v] || 'th');
}

/**
 * Regular-season table from games.json, sorted by win % (ties as half) then points for -- the
 * same order Sleeper seeds this league by (checked: every semifinal is 1 v 4 and 2 v 3).
 */
export const regularStandings = (games, year, throughWeek = null) => {
    const out = {};
    for(const g of gamesOf(games, year, ['regular'])) {
        if(throughWeek !== null && g.week > throughWeek) continue;
        const r = out[g.user_id] || (out[g.user_id] = {user_id: g.user_id, wins: 0, losses: 0, ties: 0, pf: 0, pa: 0});
        if(g.result === 'W') r.wins++;
        else if(g.result === 'L') r.losses++;
        else r.ties++;
        r.pf += g.pf;
        r.pa += g.pa;
    }
    const rows = Object.values(out);
    for(const r of rows) {
        r.pf = round2(r.pf);
        r.pa = round2(r.pa);
        const n = r.wins + r.losses + r.ties;
        r.winPct = n ? (r.wins + r.ties / 2) / n : 0;
    }
    return rows.sort((a, b) => (b.winPct - a.winPct) || (b.pf - a.pf));
}

/**
 * Final standings 1-10 with each team's regular-season record, from final_standings.
 * [] for a season that hasn't finished.
 */
export const finalTable = (history, games, year) => {
    const table = history.final_standings?.[String(year)] || [];
    const reg = {};
    regularStandings(games, year).forEach((r, i) => { reg[r.user_id] = {...r, seed: i + 1}; });
    return table.map((row) => ({...row, ...(reg[row.user_id] || {})}));
}

/**
 * Rank after every regular-season week: {weeks: [1..n], ranks: {user_id: [rank after week 1, ...]},
 * records: {user_id: ["1-0", ...]}}. Rank uses regularStandings()'s order at each week.
 */
export const ranksByWeek = (games, year) => {
    const reg = gamesOf(games, year, ['regular']);
    const weeks = [...new Set(reg.map((g) => g.week))].sort((a, b) => a - b);
    const ranks = {}, records = {};
    for(const w of weeks) {
        regularStandings(reg, year, w).forEach((r, i) => {
            (ranks[r.user_id] || (ranks[r.user_id] = [])).push(i + 1);
            const rec = r.ties ? `${r.wins}-${r.losses}-${r.ties}` : `${r.wins}-${r.losses}`;
            (records[r.user_id] || (records[r.user_id] = [])).push(rec);
        });
    }
    return {weeks, ranks, records};
}

/**
 * The season's extremes. Blowout and closest game count every played game, playoffs included,
 * from the winner's side. High and low weeks come from season-notes (three each).
 */
export const seasonExtremes = (games, notes, year) => {
    const rows = gamesOf(games, year).filter((g) => g.result === 'W');
    const margin = (g) => round2(g.pf - g.pa);
    let blowout = null, closest = null;
    for(const g of rows) {
        if(!blowout || margin(g) > margin(blowout)) blowout = g;
        if(!closest || margin(g) < margin(closest)) closest = g;
    }
    const n = notes?.seasons?.[String(year)] || {};
    return {
        blowout: blowout && {...blowout, margin: margin(blowout)},
        closest: closest && {...closest, margin: margin(closest)},
        high: n.high_weeks || [],
        low: n.low_weeks || [],
    };
}

/** Each team's top starter scorer that season (season-notes top_scorers[0]). */
export const seasonMvps = (notes, year) => {
    const ts = notes?.seasons?.[String(year)]?.top_scorers || {};
    const out = {};
    for(const [uid, list] of Object.entries(ts)) if(list?.length) out[uid] = list[0];
    return out;
}

/** The season's primary draft -- never the carried-over 2021 draft filed under 2022. */
export const seasonDraft = (history, year) =>
    (history.drafts?.[String(year)] || []).find((d) => d.primary && d.status === 'complete') || null;

/** The 2021 (ESPN) draft: the non-primary draft Sleeper files under 2022. */
export const carriedOverDraft = (history) =>
    (history.drafts?.[String(FOUNDING_SEASON + 1)] || []).find((d) => !d.primary) || null;

/** Picks of rounds 1..n, grouped by round: [[pick, ...], ...] */
export const earlyRounds = (draft, n = 3) => {
    if(!draft) return [];
    const out = [];
    for(let r = 1; r <= Math.min(n, draft.rounds); r++) {
        out.push(draft.picks.filter((p) => p.round === r).sort((a, b) => a.pick_no - b.pick_no));
    }
    return out;
}

/**
 * Keepers for a season, from keepers.json, checked against the primary draft's is_keeper flags.
 * Returns {rows, agrees}: `agrees` is false if the two sources name different players.
 */
export const seasonKeepers = (history, keepersData, year) => {
    const rows = keepersData?.keepers?.[String(year)] || [];
    const draft = seasonDraft(history, year);
    const flagged = new Set((draft?.picks || []).filter((p) => p.is_keeper).map((p) => p.player_id));
    const listed = new Set(rows.map((r) => r.player_id));
    const agrees = flagged.size === listed.size && [...listed].every((id) => flagged.has(id));
    return {rows, agrees};
}

/**
 * One card per season for /seasons: champion, runner-up, top seed, best single week.
 * In-progress seasons get the current leader and the best week so far instead.
 */
export const seasonCards = (history, games, notes) => {
    const cards = [];
    for(const year of archiveYears(history)) {
        if(year === FOUNDING_SEASON) {
            cards.push({year, kind: 'espn'});
            continue;
        }
        const complete = isComplete(history, year);
        const table = history.final_standings?.[String(year)] || [];
        const reg = regularStandings(games, year);
        const n = notes?.seasons?.[String(year)];
        cards.push({
            year,
            kind: complete ? 'complete' : 'progress',
            champion: table.find((r) => r.place === 1)?.user_id || null,
            runnerUp: table.find((r) => r.place === 2)?.user_id || null,
            topSeed: reg[0] || null,
            bestWeek: n?.high_weeks?.[0] || null,
            throughWeek: n?.through_week ?? null,
        });
    }
    return cards;
}

/** The title game from the champion's side: {week, pf, pa, opponent_id}, or null. */
export const titleGame = (history, games, year) => {
    const champ = history.final_standings?.[String(year)]?.find((r) => r.place === 1)?.user_id;
    if(!champ) return null;
    return games.find((g) => g.season === Number(year) && g.kind === 'playoff' &&
        g.user_id === champ && g.week === Math.max(...gamesOf(games, year, ['playoff']).map((x) => x.week))) || null;
}
