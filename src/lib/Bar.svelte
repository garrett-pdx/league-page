<script>
	import { getAvatarFromTeamManagers, getTeamNameFromTeamManagers, round } from "./utils/helperFunctions/universalFunctions";
    import { managerHref } from "./utils/managerLink";


    let {leagueTeamManagers, stat, label, xMin, xMax, secondStat, managerID, rosterID, color, year} = $props();

    let user = $derived(managerID ? leagueTeamManagers.users[managerID] : null);
    let href = $derived(managerHref({year, leagueTeamManagers, managerID, rosterID}));
</script>

<style>
    :global(.opacity) {
        opacity: 0.3;
    }

    .barParent {
        position: relative;
        margin-bottom: -10px;
        height: 76px;
    }

    .managerName {
        position: absolute;
        top: 0;
        left: 80px;
    }

	.teamAvatar {
        position: absolute;
        left: 20px;
        top: 0;
        bottom: 0;
        height: 40px;
        margin: auto;
		border-radius: 50%;
		border: 2px solid;
        z-index: 14;
        background-color: #fff;
	}

    .statBars {
        display: flex;
        margin: 0 auto;
    }

    .leftSpacer {
        width: 40px;
        height: 1px;
        display: inline-block;
    }

    .rightSpacer {
        width: 20px;
        height: 1px;
        display: inline-block;
    }

    .bars {
        flex-grow: 2;
        position: relative;
    }

    .bar {
        height: 1.8em;
        border-radius: 0 0.9em 0.9em 0;
        z-index: 10;
    }

    .secondBar {
        position: absolute;
        top: 0;
        z-index: 11;
        left: 0;
    }

    .barLabel {
        z-index: 12;
        vertical-align: text-top;
        margin-left: 40px;
    }

    .vCenter {
        display: block;
        height: 1.8em;
        position: absolute;
        width: 100%;
        top: 0;
        bottom: 0;
        margin: auto 0;
    }

    .clickable {
        cursor: pointer;
    }

    /* The name is a link that looks like the plain text it replaced; the avatar's link is a
       second way in for a mouse, skipped by the keyboard so each bar has one stop. */
    a.managerName {
        color: inherit;
        text-decoration: none;
        /* extra hit area above and below the text; the margin keeps the text where it was */
        padding: 10px 0;
        margin: -10px 0;
    }

    a.managerName:hover {
        text-decoration: underline;
    }

    a.managerName:focus-visible {
        outline: 2px solid var(--blueOne);
        outline-offset: 2px;
    }

    @media (max-width: 600px) {
        .barParent {
            /* margin-bottom: -10px; */
            height: 57px;
        }
        .managerName {
            left: 60px;
            font-size: 0.8em;
        }
        .teamAvatar {
            left: 10px;
            height: 30px;
        }
        .barLabel {
            margin-left: 30px;
            vertical-align: middle;
            font-size: 0.8em;
        }
        .leftSpacer {
            width: 30px;
        }
        .rightSpacer {
            width: 10px;
        }
        .bar {
            height: 1.2em;
            border-radius: 0 0.6em 0.6em 0;
        }
        .vCenter {
            height: 1.2em;
        }
    }
</style>

<div class="barParent">
    <a {href} tabindex="-1" aria-hidden="true"><img alt="team avatar" style="border-color: var({color});" class="teamAvatar clickable" src="{user ? `https://sleepercdn.com/avatars/thumbs/${user.avatar}` : getAvatarFromTeamManagers(leagueTeamManagers, rosterID, year)}" /></a>
    <a {href} class="managerName clickable">
        {#if user}
            {user.display_name}
        {:else if rosterID}
            {getTeamNameFromTeamManagers(leagueTeamManagers, rosterID, year)}
        {/if}
    </a>
    <div class="vCenter">
        <div class="statBars">
            <div class="leftSpacer" />
            <div class="bars">
                <div class="bar{!secondStat  ? '' : ' opacity'}" style="background-color: var({color}); width: {(stat - xMin) / (xMax - xMin == 0 ? 1 : (xMax - xMin)) * 100}%;">
                    {#if !secondStat}
                        <span class="barLabel">{stat}{label}</span>
                    {/if}
                </div>
                {#if secondStat}
                    <div class="bar secondBar" style="background-color: var({color}); width: {(secondStat - xMin) / (xMax - xMin == 0 ? 1 : (xMax - xMin)) * 100}%;">
                        <span class="barLabel">{secondStat}&nbsp;&nbsp;of&nbsp;&nbsp;{stat}&nbsp;&nbsp;({round(secondStat/stat*100)}%)</span>
                    </div>
                {/if}
            </div>
            <div class="rightSpacer" />
        </div>
    </div>
</div>