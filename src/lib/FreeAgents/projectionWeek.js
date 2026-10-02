/*
Which week's projections Free Agents should show.

Sleeper's /state/nfl advances its week on WEDNESDAY around 3 AM ET (midnight Pacific, with the
overnight waiver run) -- inferred from this league's transaction timestamps, where every rollover
in 2025 and 2026 lands late Tuesday to early Wednesday (twice as late as Thursday), and documented
nowhere by Sleeper. The NFL week itself ends with Monday night's game. So for a day or more Sleeper
still says "week N" about games that are all over, and the page would show projections for games
already played -- right when people are planning pickups.

So we also count weeks off the calendar, each starting 12 AM ET Tuesday (week 1 starts the Tuesday
on or before Sleeper's season_start_date), and show whichever is LATER. Taking the max can never
double-count once Sleeper catches up, and it covers however late Sleeper's rollover runs. A rare
Tuesday makeup game would make this jump a day early.
*/
const DAY = 24 * 3600 * 1000;

const ET = new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/New_York',
    year: 'numeric', month: 'numeric', day: 'numeric',
    hour: 'numeric', minute: 'numeric', hourCycle: 'h23',
});

// ET wall-clock time, expressed as a UTC timestamp, so date arithmetic ignores DST
const etWallClock = (date) => {
    const p = Object.fromEntries(ET.formatToParts(date).map((x) => [x.type, parseInt(x.value)]));
    return Date.UTC(p.year, p.month - 1, p.day, p.hour, p.minute);
};

export const projectionWeek = (nflState, now = new Date()) => {
    const week = nflState.display_week ?? nflState.week ?? 0;
    if(!week || nflState.season_type != 'regular' || !nflState.season_start_date) return week;

    const start = new Date(`${nflState.season_start_date}T00:00:00Z`);
    start.setUTCDate(start.getUTCDate() - ((start.getUTCDay() - 2 + 7) % 7)); // back to Tuesday
    const calendarWeek = Math.floor((etWallClock(now) - start.getTime()) / (7 * DAY)) + 1;

    // never more than one ahead of Sleeper, in case the calendar and Sleeper disagree about week 1
    return Math.max(week, Math.min(calendarWeek, week + 1));
}
