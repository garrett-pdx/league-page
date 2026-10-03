<script>
	import LinearProgress from '@smui/linear-progress';
	import { getNflState, leagueName, getAwards, getLeagueTeamManagers, homepageText, managers, gotoManager, enableBlog, waitForAll, getUpcomingDraft } from '$lib/utils/helper';
	import { Transactions, PowerRankings, HomePost} from '$lib/components';
	import { Countdown } from '$lib/Design';
	import { getAvatarFromTeamManagers, getTeamFromTeamManagers } from '$lib/utils/helperFunctions/universalFunctions';
    import { managerHref } from '$lib/utils/managerLink';

    const nflState = getNflState();
    const podiumsData = getAwards();
    const leagueTeamManagersData = getLeagueTeamManagers();
    // startTime is null once the draft completes -- see the note in leagueDrafts.js.
    const draftData = getUpcomingDraft();
</script>

<style>
    #home {
        display: flex;
        flex-wrap: nowrap;
        position: relative;
        overflow-y: hidden;
        z-index: 1;
    }

    #main {
        flex-grow: 1;
        min-width: 320px;
        margin: 0 auto;
        padding: 60px 0;
    }

    .text {
        padding: 0 30px;
        max-width: 620px;
        margin: 0 auto;
    }

    .leagueData {
        position: relative;
        z-index: 1;
        width: 100%;
        min-width: 470px;
        max-width: 470px;
        min-height: 100%;
		background-color: var(--ebebeb);
        border-left: var(--eee);
		box-shadow: inset 8px 0px 6px -6px rgb(0 0 0 / 24%);
    }

    @media (max-width: 950px) {
        .leagueData {
            max-width: 100%;
            min-width: 100%;
            width: 100%;
		    box-shadow: none;
        }
        #home {
            flex-wrap: wrap;
        }
    }

    .transactions {
        display: block;
        width: 95%;
        margin: 10px auto;
    }

    /*
    Phones: one column, in reading order. Stacked as two boxes, the right rail fell below
    everything in the left column, so the champion sat ~2,400px down, under the intro, the
    latest blog post and the power rankings. Dissolving both columns (display: contents) makes
    every block a flex item of #home, and `order` interleaves them: intro, week banner, draft
    countdown, power rankings, champion, blog post, transactions. Desktop is untouched.
    */
    @media (max-width: 950px) {
        #home { flex-direction: column; }
        #main, .leagueData { display: contents; }
        .text { order: 1; padding-top: 40px; padding-bottom: 20px; }
        .homeBanner { order: 2; }
        .nextEvent { order: 3; }
        .rankings { order: 4; padding-bottom: 20px; }
        #currentChamp { order: 5; }
        .text.homePost { order: 6; padding-top: 0; }
        .transactions { order: 7; }
    }

    .center {
        text-align: center;
    }

    h6 {
        text-align: center;
    }

    .homeBanner {
        background-color: var(--blueOne);
        color: #fff;
        padding: 0.5em 0;
        font-weight: 500;
        font-size: 1.5em;
    }

    .hero {
        text-align: center;
        margin: 0 0 1.5em;
    }

    .leagueTitle {
        /* h1 inherits MDC's headline1 at 96px -- set our own size, as every heading here does */
        font-family: var(--fontDisplay);
        font-size: 2.6em;
        font-weight: 600;
        line-height: 1;
        letter-spacing: 0.01em;
        text-transform: uppercase;
        color: var(--navy700);
        margin: 0;
    }

    .heroRule {
        display: block;
        width: 3.5em;
        height: 3px;
        margin: 0.5em auto 0;
        border-radius: var(--radiusPill);
        background-color: var(--goldFill);
    }

    .nextEvent {
        padding: 1.1em 0.5em;
        background-color: var(--fff);
        border-bottom: 1px solid var(--ddd);
    }

    /* champ styling */
    #currentChamp {
        padding: 25px 0;
		background-color: var(--f3f3f3);
        box-shadow: 5px 0 8px var(--champShadow);
        border-left: 1px solid var(--ddd);
    }

    /* One link around the champion's photo and team name, so it is a single stop for the keyboard. */
    .champLink {
        display: block;
        color: inherit;
        text-decoration: none;
    }

    .champLink:focus-visible, .bannerLink:focus-visible {
        outline: 2px solid var(--blueTwo);
        outline-offset: -4px;
    }

    /* The banner's own padding moves onto the link, so the whole bar is the hit area. */
    .bannerLink {
        display: block;
        color: inherit;
        text-decoration: none;
        padding: 0.5em 0;
        margin: -0.5em 0;
    }

    #champ {
        position: relative;
        width: 150px;
        height: 150px;
        margin: 0 auto;
        cursor: pointer;
    }

    .first {
        position: absolute;
        transform: translate(-50%, -50%);
        width: 80px;
        height: 80px;
        border-radius: 100%;
        border: 1px solid var(--ccc);
        left: 50%;
        top: 43%;
    }

    .laurel {
        position: absolute;
        transform: translate(-50%, -50%);
        width: 135px;
        height: auto;
        left: 50%;
        /* Was 50%, seven points below .first's 43% -- the wreath rang the photo off-centre,
           dangling well past the chin with barely any clearance above the hairline. laurel.svg
           is a closed ring (the two branches cross at the bottom), so it wants to centre ON
           the avatar, not below it; matching .first's anchor does that. */
        top: 43%;
    }

    h4 {
        text-align: center;
        font-size: 1.8em;
        margin: 10px;
        font-style: italic;
    }

    .label {
        display: table;
        text-align: center;
        line-height: 1.1em;
        font-size: 1.7em;
        margin: 6px auto 10px;
        cursor: pointer;
    }
    
	:global(.curOwner) {
		font-size: 0.75em;
		color: #bbb;
		font-style: italic;
	}
</style>

<div id="home">
    <div id="main">
        <div class="text">
            <div class="hero">
                <h1 class="leagueTitle">{leagueName}</h1>
                <span class="heroRule"></span>
            </div>
            <!-- homepageText contains the intro text for your league, this gets edited in /src/lib/utils/leagueInfo.js -->
            {@html homepageText }
        </div>
        <!-- Most recent Blog Post (if enabled). Its own .text block, not inside the one above, so
             phones can move it below the rankings and the champion (see the order rules). -->
        {#if enableBlog}
            <div class="text homePost">
                <HomePost />
            </div>
        {/if}
        <div class="rankings">
            <PowerRankings />
        </div>
    </div>
    
    <div class="leagueData">
        <div class="homeBanner">
            {#await nflState}
                <div class="center">Retrieving NFL state...</div>
                <LinearProgress indeterminate />
            {:then nflStateData}
                <a class="bannerLink" href="/matchups">
                <div class="center">NFL {nflStateData.season} 
                    {#if nflStateData.season_type == 'pre'}
                        Preseason
                    {:else if nflStateData.season_type == 'post'}
                        Postseason
                    {:else}
                        Season - {nflStateData.week > 0 ? `Week ${nflStateData.week}` : "Preseason"}
                    {/if}
                </div>
                </a>
            {:catch error}
                <div class="center">Something went wrong: {error.message}</div>
            {/await}
        </div>

        {#await draftData then draft}
            {#if draft?.startTime}
                <div class="nextEvent">
                    <Countdown
                        target={draft.startTime}
                        label="{draft.year} Draft"
                        expiredLabel="Drafting now"
                    />
                </div>
            {/if}
        {:catch}
            <!-- the countdown is decoration; a failed draft fetch should not take the page down -->
        {/await}

        <div id="currentChamp">
            {#await waitForAll(podiumsData, leagueTeamManagersData)}
                <p class="center">Retrieving awards...</p>
                <LinearProgress indeterminate />
            {:then [podiums, leagueTeamManagers]}
                {#if podiums[0]}
                    <h4>{podiums[0].year} Fantasy Champ</h4>
                    <a class="champLink" href={managerHref({year: podiums[0].year, leagueTeamManagers, rosterID: parseInt(podiums[0].champion)})}>
                        <div id="champ">
                            <img src="{getAvatarFromTeamManagers(leagueTeamManagers, podiums[0].champion, podiums[0].year)}" class="first" alt="champion" />
                            <img src="/brand/laurel.svg" class="laurel" alt="laurel" />
                        </div>
                        <span class="label">{getTeamFromTeamManagers(leagueTeamManagers, podiums[0].champion, podiums[0].year).name}</span>
                    </a>
                {:else}
                    <p class="center">No former champs.</p>
                {/if}
            {:catch error}
                <p class="center">Something went wrong: {error.message}</p>
            {/await}
        </div>

        <div class="transactions" >
            <Transactions />
        </div>
    </div>
</div>