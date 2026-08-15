<script>
    import { goto } from "$app/navigation";
	import { getDatesActive, getRosterIDFromManagerID, getDistinctTeamName } from "$lib/utils/helperFunctions/universalFunctions";

    export let manager, leagueTeamManagers, key;

    let retired = false;

    // manager.roster is deprecated, pages should be using managerID now
    let rosterID = manager.roster;
    let year = null;

    if(manager.managerID) {
        const dates = getDatesActive(leagueTeamManagers, manager.managerID);
        if(dates.end) retired = true;

        ({rosterID, year} = getRosterIDFromManagerID(leagueTeamManagers, manager.managerID) || {rosterID, year});
    }

    const commissioner = manager.managerID ? leagueTeamManagers.users[manager.managerID].is_owner : false;

    const teamName = getDistinctTeamName(leagueTeamManagers, rosterID, year, manager.name);

    /*
    The franchise leads and the person is the subtitle, which is how every league site
    worth copying does it. Three managers have never set a team name on Sleeper, so fall
    back to leading with the person rather than printing an empty headline.
    */
    const headline = teamName || manager.name;
    const subline = teamName ? manager.name : (manager.location || null);

    // The card is the directory's primary navigation but is a div, so it needs button
    // semantics and the Enter/Space activation a real button would have.
    const openManager = () => goto(`/manager?manager=${key}`);
    const onRowKey = (e) => {
        if(e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            openManager();
        }
    }
</script>

<style>
    .card {
        position: relative;
        display: block;
        width: 100%;
        aspect-ratio: 1 / 1;
        border-radius: var(--radiusMd);
        overflow: hidden;
        background-color: var(--eee);
        box-shadow: var(--shadowCard);
        cursor: pointer;
        transition: box-shadow 0.18s ease, transform 0.18s ease;
    }

    /* Gate the lift behind a real pointer -- on touch it sticks after the tap. */
    @media (hover: hover) {
        .card:hover {
            box-shadow: var(--shadowCardHover);
            transform: translateY(-3px);
        }

        .card:hover .photo { transform: scale(1.04); }
    }

    .card:focus-visible {
        outline: 3px solid var(--blueOne);
        outline-offset: 2px;
    }

    .photo {
        display: block;
        width: 100%;
        height: 100%;
        object-fit: cover;
        transition: transform 0.35s ease;
    }

    /*
    Manager photos are arbitrary snapshots, so text can never rely on the image behind it.
    The scrim is opaque enough at the baseline that white copy clears AA regardless of what
    the photo happens to be.
    */
    .scrim {
        position: absolute;
        left: 0;
        right: 0;
        bottom: 0;
        padding: 2.6em 0.85em 0.8em;
        background: linear-gradient(
            to top,
            rgba(0, 0, 0, 0.92) 0%,
            rgba(0, 0, 0, 0.75) 45%,
            rgba(0, 0, 0, 0.35) 75%,
            rgba(0, 0, 0, 0) 100%
        );
        pointer-events: none;
    }

    /*
    Team names here run from "#FREEJT" to "JustHereSoIWon'tGetFined" -- a single 24-character
    token with no break opportunity. It has to wrap mid-word or it overflows the card, so clamp
    to two lines and let the rest ellipsise rather than letting it eat the portrait.
    */
    .headline {
        display: -webkit-box;
        -webkit-line-clamp: 2;
        line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        font-family: var(--fontDisplay);
        font-weight: 600;
        font-size: 0.95em;
        line-height: 1.1;
        text-transform: uppercase;
        letter-spacing: 0.02em;
        color: #fff;
        overflow-wrap: anywhere;
    }

    .subline {
        display: block;
        margin-top: 0.2em;
        font-size: 0.74em;
        line-height: 1.2;
        color: rgba(255, 255, 255, 0.88);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .badges {
        position: absolute;
        top: 0.6em;
        left: 0.6em;
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        gap: 0.35em;
    }

    .badge {
        font-family: var(--fontDisplay);
        font-size: 0.62em;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        padding: 0.32em 0.7em;
        border-radius: var(--radiusPill);
        line-height: 1;
        white-space: nowrap;
    }

    .commish {
        background-color: var(--goldFill);
        color: var(--goldOnFill);
    }

    .retired {
        background-color: rgba(255, 255, 255, 0.92);
        color: var(--navy700);
    }

    /* A departed manager's photo is desaturated so the Moratorium reads at a glance. */
    .isRetired .photo {
        filter: grayscale(0.85);
    }

    @media (max-width: 420px) {
        .headline { font-size: 0.95em; }
        .subline { font-size: 0.72em; }
        .scrim { padding: 2.2em 0.6em 0.65em; }
    }
</style>

<div
    class="card"
    class:isRetired={retired}
    role="button"
    tabindex="0"
    aria-label="{manager.name}{teamName ? `, ${teamName}` : ''}"
    onclick={openManager}
    onkeydown={onRowKey}
>
    <img class="photo" src="{manager.photo}" alt="{manager.name}" loading="lazy" />

    {#if commissioner || retired}
        <div class="badges">
            {#if commissioner}
                <span class="badge commish">Commissioner</span>
            {/if}
            {#if retired}
                <span class="badge retired">Moratorium</span>
            {/if}
        </div>
    {/if}

    <div class="scrim">
        <span class="headline">{headline}</span>
        {#if subline}
            <span class="subline">{subline}</span>
        {/if}
    </div>
</div>
