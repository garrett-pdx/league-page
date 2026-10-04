/*
The Seasons archive's numbers, as pure functions over the committed dataset: league-history.json,
games.json (decoded by getLeagueGames), season-notes.json and keepers.json. No Svelte, no fetch,
no $lib imports, so Node can import and check it directly.

Three traps this file exists to keep in one place:

  * ROSTER IDS MOVE BETWEEN SEASONS. A bracket row carries roster IDs, which mean something only
    inside their own season; they become user_ids through managers[uid].records[season].roster_id
    for THAT season. rosterUsers() is the only place that join happens.
  * AN IMPORTED DRAFT IS NOT A SLEEPER SEASON'S DRAFT. A league that came to Sleeper from
    another platform can import its last draft there, and Sleeper files it under the first
    Sleeper season as a second draft. The `primary` one is that season's own draft;
    seasonDraft() takes the primary only, and importedDraft() finds the other by the ID that
    league.json's history.preSleeper names.
  * AN UNPLAYED SEASON LOOKS REAL. final_standings only holds completed seasons, so "is there a
    final table" is the test for "is this season finished" -- never "is there a season entry".

Seasons played before Sleeper (league.json history.preSleeper) are passed in by the caller as
`preSleeper`, so this file stays free of $lib imports.
*/

const round2 = (n) => Math.round(n * 100) / 100;

/** Every year with a page, newest first: the Sleeper seasons plus any played before Sleeper. */
export const archiveYears = (history, preSleeper = []) => {
    const years = Object.keys(history.seasons || {}).map(Number);
    for(const s of preSleeper) years.push(Number(s.season));
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
/**
 * Seeds for a season: regularStandings() order, except that in a league with divisions the
 * division winners take the top seeds (in that order) and everyone else follows, which is how
 * Sleeper seeds by default. [{user_id, ...}] best seed first.
 */
export const seedOrder = (history, games, year) => {
    const season = history.seasons?.[String(year)];
    // Sleeper seeds from its own settled records, which can sit a game away from what the weekly
    // scores now say (a stat correction after settlement); use them when every team has one.
    const fromGames = regularStandings(games, year);
    const recs = fromGames.map((r) => history.managers?.[r.user_id]?.records?.[String(year)]);
    const rows = recs.every(Boolean) ? fromGames.map((r, i) => ({
        ...r, wins: recs[i].wins || 0, losses: recs[i].losses || 0, ties: recs[i].ties || 0,
        pf: recs[i].points_for ?? r.pf,
    })).map((r) => ({...r, winPct: (r.wins + r.losses + r.ties) ? (r.wins + r.ties / 2) / (r.wins + r.losses + r.ties) : 0}))
        .sort((a, b) => (b.winPct - a.winPct) || (b.pf - a.pf)) : fromGames;
    if(!season?.divisions || season.divisions < 2) return rows;
    const division = (uid) => history.managers?.[uid]?.records?.[String(year)]?.division;
    const seen = new Set();
    const winners = rows.filter((r) => {
        const d = division(r.user_id);
        if(d === null || d === undefined || seen.has(d)) return false;
        seen.add(d);
        return true;
    });
    return [...winners, ...rows.filter((r) => !winners.includes(r))];
}

/**
 * {round: [week, ...]} for a season's bracket. Sleeper's playoff_round_type: 0 one week per
 * round, 1 one week per round but a two-week final, 2 two weeks per round. Both brackets run on
 * the winners bracket's calendar.
 */
export const roundWeeks = (season, winners) => {
    const type = season.playoff_round_type || 0;
    const rounds = Math.max(0, ...(winners || []).map((m) => m.r || 0));
    const out = {};
    let week = season.playoff_week_start;
    for(let r = 1; r <= rounds; r++) {
        const n = type === 2 || (type === 1 && r === rounds) ? 2 : 1;
        out[r] = Array.from({length: n}, (_, i) => week + i);
        week += n;
    }
    return out;
}

const weeksLabel = (weeks) => weeks.length > 1 ? `weeks ${weeks[0]}–${weeks[weeks.length - 1]}` : `week ${weeks[0]}`;

// A's points and B's over every leg of a round; null if a leg hasn't been played.
const legScores = (games, year, weeks, a, b) => {
    let pf = 0, pa = 0;
    for(const week of weeks) {
        const row = findGame(games, year, week, a, b);
        if(!row) return null;
        pf += row.pf;
        pa += row.pa;
    }
    return {pf: round2(pf), pa: round2(pa)};
}

/**
 * Both brackets for a season, ready to draw: rounds of games with each side's seed and points,
 * from league-history.json's bracket rows (roster IDs, mapped through that season) and games.json.
 *
 * The losers bracket comes in two kinds (playoff_type). A consolation bracket (1) decides the
 * places straight after the playoff teams, winners advancing. A toilet bowl (0) is played to
 * escape last place: Sleeper records the LOWER scorer as `w`, and its final decides last.
 * Data pulled before the field existed is read as a consolation bracket.
 */
export const seasonBracket = (history, games, year) => {
    const y = String(year);
    const raw = history.brackets?.[y];
    const season = history.seasons?.[y];
    if(!raw || !season) return null;

    const users = rosterUsers(history, y);
    const seeds = {};
    seedOrder(history, games, year).forEach((r, i) => { seeds[r.user_id] = i + 1; });
    const weeksOf = roundWeeks(season, raw.winners);
    const rounds = Object.keys(weeksOf).length;
    const teams = season.teams || Object.keys(users).length;
    const playoffTeams = season.playoff_teams || 0;
    const toiletBowl = (season.playoff_type ?? 1) === 0;

    const placeName = (p) => p === 1 ? 'Championship' : p === teams ? 'Last place' : `${ordinalWord(p)} place`;
    const roundName = (r, plural) => {
        const fromEnd = rounds - r;
        if(fromEnd === 0) return plural ? 'Finals' : 'Final';
        if(fromEnd === 1) return plural ? 'Semifinals' : 'Semifinal';
        if(fromEnd === 2) return plural ? 'Quarterfinals' : 'Quarterfinal';
        return `Round ${r}`;
    };

    const build = (rows, side) => {
        const byRound = {};
        for(const m of rows || []) {
            const a = users[m.t1], b = users[m.t2];
            if(!a || !b) continue;
            const weeks = weeksOf[m.r] || [season.playoff_week_start + m.r - 1];
            const score = legScores(games, y, weeks, a, b);
            // The side that won the game on the scoreboard. In a toilet bowl that is `l`.
            const winner = side === 'losers' && toiletBowl ? (m.l ? users[m.l] : null) : (m.w ? users[m.w] : null);
            let place = null, label;
            if(m.p && side === 'winners') { place = m.p; label = placeName(place); }
            else if(m.p && !toiletBowl) { place = playoffTeams + m.p; label = placeName(place); }
            else if(m.p) { place = teams - m.p; label = m.p === 1 ? 'Last place' : `${ordinalWord(place)} place`; }
            else label = side === 'winners' ? roundName(m.r, false) : (toiletBowl ? 'Toilet bowl' : 'Consolation');
            const game = {
                week: weeks[weeks.length - 1],
                weeks,
                place,
                label,
                a: {user_id: a, seed: seeds[a], pf: score ? score.pf : null, won: winner === a},
                b: {user_id: b, seed: seeds[b], pf: score ? score.pa : null, won: winner === b},
            };
            (byRound[m.r] || (byRound[m.r] = [])).push(game);
        }
        return Object.keys(byRound).map(Number).sort((p, q) => p - q).map((r) => {
            const weeks = weeksLabel(weeksOf[r] || [season.playoff_week_start + r - 1]);
            const name = side === 'winners' ? roundName(r, true)
                : r === rounds ? (toiletBowl ? 'Toilet bowl final' : 'Placement games') : (toiletBowl ? 'Toilet bowl' : 'Consolation');
            return {
                label: `${name} · ${weeks}`,
                // the title game first, then third place
                games: byRound[r].sort((p, q) => (p.place ?? 0) - (q.place ?? 0)),
            };
        });
    };

    return {
        winners: build(raw.winners, 'winners'),
        losers: build(raw.losers, 'losers'),
        losersTitle: toiletBowl ? 'Toilet bowl' : 'Consolation bracket',
    };
}

const ordinalWord = (n) => {
    const v = n % 100;
    return n + (['th', 'st', 'nd', 'rd'][(v - 20) % 10] || ['th', 'st', 'nd', 'rd'][v] || 'th');
}

/**
 * Regular-season table from games.json, sorted by win % (ties as half) then points for, which is
 * Sleeper's default seeding. It knows nothing of divisions: in a league with them, Sleeper seeds
 * division winners first.
 */
export const regularStandings = (games, year, throughWeek = null) => {
    const out = {};
    for(const g of gamesOf(games, year, ['regular'])) {
        if(throughWeek !== null && g.week > throughWeek) continue;
        const r = out[g.user_id] || (out[g.user_id] = {user_id: g.user_id, wins: 0, losses: 0, ties: 0, pf: 0, pa: 0});
        // A median-game result is a second result that week, counted as Sleeper counts it.
        for(const res of g.median ? [g.result, g.median] : [g.result]) {
            if(res === 'W') r.wins++;
            else if(res === 'L') r.losses++;
            else r.ties++;
        }
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
    regularStandings(games, year).forEach((r) => { reg[r.user_id] = r; });
    seedOrder(history, games, year).forEach((r, i) => { if(reg[r.user_id]) reg[r.user_id] = {...reg[r.user_id], seed: i + 1}; });
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

/** The season's primary draft -- never a draft imported from another platform. */
export const seasonDraft = (history, year) =>
    (history.drafts?.[String(year)] || []).find((d) => d.primary && d.status === 'complete') || null;

/** A pre-Sleeper season's imported draft, found by league.json's importedDraftId. */
export const importedDraft = (history, pre) => {
    if(!pre?.importedDraftId) return null;
    for(const list of Object.values(history.drafts || {})) {
        const found = list.find((d) => d.draft_id === pre.importedDraftId);
        if(found) return found;
    }
    return null;
}

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
export const seasonCards = (history, games, notes, preSleeper = []) => {
    const cards = [];
    for(const year of archiveYears(history, preSleeper)) {
        const pre = preSleeper.find((s) => Number(s.season) === year);
        if(pre && !history.seasons?.[String(year)]) {
            cards.push({year, kind: 'pre', platform: pre.platform, text: pre.card || null, hasDraft: Boolean(pre.importedDraftId)});
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

/**
 * The title game from the champion's side: {week, weeks, pf, pa, opponent_id}, or null. Read from
 * the bracket's p=1 game, so a final played over two weeks is scored over both.
 */
export const titleGame = (history, games, year) => {
    const y = String(year);
    const champ = history.final_standings?.[y]?.find((r) => r.place === 1)?.user_id;
    const season = history.seasons?.[y];
    const winners = history.brackets?.[y]?.winners;
    if(!champ || !season || !winners) return null;
    const users = rosterUsers(history, y);
    const final = winners.find((m) => m.p === 1 && (users[m.t1] === champ || users[m.t2] === champ));
    if(!final) return null;
    const opponent = users[final.t1] === champ ? users[final.t2] : users[final.t1];
    const weeks = roundWeeks(season, winners)[final.r] || [season.playoff_week_start + final.r - 1];
    const score = legScores(games, y, weeks, champ, opponent);
    if(!score) return null;
    return {week: weeks[weeks.length - 1], weeks, pf: score.pf, pa: score.pa, opponent_id: opponent};
}
