<script>
    import { getLeagueData, waitForAll } from '$lib/utils/helper';

    /*
    The home page's in-season "what's next" line: the trade deadline, then the playoffs, then
    nothing. It takes over from the draft countdown in the same spot of the right rail once the
    draft is done and, like that countdown, renders nothing at all (no placeholder, no spinner)
    until it has something true to say, and nothing if a fetch fails.

    WHY THIS DOES NOT TICK. The plan was to reuse $lib/Design's Countdown here, and it would have,
    given a timestamp. There isn't a reliable one:

      * Sleeper's trade deadline is not a time of day. Its help article "When is my trade
        deadline?" (https://support.sleeper.com/en/articles/2435411-when-is-my-trade-deadline,
        read 2026-10-03) says trading stays open through every game of the deadline week and
        "closes as soon as the final game finishes". That is whenever week 12's last game
        actually ends, which no API publishes in advance.
      * The public API (api.sleeper.app/v1/state/nfl) gives `season_start_date` -- a calendar
        date, the Wednesday Sleeper's week 1 begins -- and the current week number. Nothing in
        it, or in the league object, carries a kickoff time for week 13 or week 16. The
        undocumented api.sleeper.com/schedule endpoint lists game dates without times.

    So the line names the week and counts weeks, both of which ARE reliable: the deadline week
    and the playoff start come from the league's own settings (`trade_deadline`,
    `playoff_week_start`), and the current week from nflState. Nothing here is hard-coded to 12
    or 16; if the league votes to move either, this follows Sleeper.

    One known soft edge: Sleeper's week number rolls over on Wednesday, so for the day or so
    between week 12's last game and that rollover the line still reads "this week". "End of
    week 12" stays true throughout; only the distance is a day stale.
    */
    let { nflState } = $props();

    const leagueData = getLeagueData();

    const weeksAway = (n) => n <= 0 ? 'this week' : n === 1 ? 'next week' : `${n} weeks away`;

    const milestone = (nfl, league) => {
        // Sleeper's league status runs pre_draft -> drafting -> in_season -> complete. Before and
        // during the draft the draft countdown owns this spot; after the final it is the offseason.
        // Read from the league object rather than getUpcomingDraft(), which is the slowest fetch
        // on the page: resolving with nflState keeps this from shoving the champion down late.
        if(league?.status !== 'in_season') return null;
        // Out of season the league object is last year's; say nothing rather than something stale.
        if(String(league?.season) !== String(nfl?.season)) return null;
        if(nfl.season_type !== 'pre' && nfl.season_type !== 'regular') return null;

        // Sleeper counts preseason weeks too; before week 1 every regular-season week is ahead.
        const week = nfl.season_type === 'pre' ? 0 : nfl.week;
        const deadline = league.settings?.trade_deadline;
        const playoffs = league.settings?.playoff_week_start;
        const tradesOn = deadline > 0 && !league.settings?.disable_trades;

        if(tradesOn && week <= deadline) {
            return {
                // "End of week 12" is Sleeper's own rule: trading closes when that week's last game does.
                label: `Trade deadline · ${weeksAway(deadline - week)}`,
                value: `End of week ${deadline}`,
            };
        }
        if(playoffs > 0 && week < playoffs) {
            return {
                label: `Playoffs · ${weeksAway(playoffs - week)}`,
                value: `Week ${playoffs}`,
            };
        }
        // Playoffs under way: nothing left to count down to.
        return null;
    };
</script>

<style>
    /* Matches .nextEvent in routes/+page.svelte and the type of $lib/Design/Countdown, so the
       draft countdown and this line read as the same slot. */
    .milestone {
        padding: 0.9em 0.5em;
        background-color: var(--fff);
        border-bottom: 1px solid var(--ddd);
        text-align: center;
    }

    .label {
        display: block;
        font-family: var(--fontDisplay);
        font-size: 0.8em;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.16em;
        color: var(--g555);
        margin-bottom: 0.4em;
    }

    .value {
        display: block;
        font-family: var(--fontDisplay);
        font-size: 1.4em;
        font-weight: 600;
        line-height: 1.1;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: var(--navy700);
    }
</style>

{#await waitForAll(nflState, leagueData) then [nfl, league]}
    {@const next = milestone(nfl, league)}
    {#if next}
        <div class="milestone">
            <span class="label">{next.label}</span>
            <span class="value">{next.value}</span>
        </div>
    {/if}
{:catch}
    <!-- decoration, like the draft countdown: a failed fetch should not take the page down -->
{/await}
