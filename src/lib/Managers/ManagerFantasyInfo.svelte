<script>
    import { managers } from '$lib/utils/leagueInfo';

    export let viewManager, players;

    /*
    The Rival tile is a real link to the rival's own page, and a second link under it goes to the
    pair's Head-to-head on /rivalry. `rival.link` is an index into `managers`; null (Jordan Leonard,
    "The Field") goes to the directory, as the old click handler did. The rivalry page takes
    Sleeper user_ids, hence managerID rather than the index.
    */
    $: rivalLink = viewManager.rival.link;
    $: rivalManager = rivalLink !== null && rivalLink >= 0 && rivalLink < managers.length ? managers[rivalLink] : null;
    $: rivalHref = rivalManager ? `/manager?manager=${rivalLink}` : '/managers';
    $: headToHeadHref = rivalManager && rivalManager.managerID && viewManager.managerID
        ? `/rivalry?player_one=${viewManager.managerID}&player_two=${rivalManager.managerID}`
        : null;
</script>

<style>
    .fantasyInfos {
        display: flex;
        justify-content: space-around;
        align-items: flex-start;
        flex-wrap: wrap;
        padding: 0 0 2em;
        margin: 3em 0 4em;
        border-bottom: 1px solid var(--aaa);
        border-top: 1px solid var(--aaa);
        box-shadow: 0 0 8px 4px var(--ccc);
    }

    .infoSlot {
        text-align: center;
        margin: 2em 1em 0;
    }

    .infoIcon {
        display: inline-flex;
        height: 70px;
        width: 70px;
        justify-content: center;
        align-items: center;
        border-radius: 100%;
        border: 1px solid var(--ccc);
        overflow: hidden;
        background-color: var(--fff);
		transition: box-shadow 0.4s;
    }

    .playerIcon {
        align-items:flex-end;
    }

    .infoLabel {
        font-size: 12px;
        color: var(--accentInk);
        font-weight: 700;
        margin-bottom: 1em;
        height: 3.6em;
        width: 100px;
        text-align: center;
        line-height: 1.2em;
    }

    .infoAnswer {
        font-size: 12px;
        color: var(--g555);
        margin-top: 1em;
        width: 90px;
        text-align: center;
        line-height: 1.2em;
    }

    .tradingScale {
        line-height: 70px;
        font-size: 55px;
        color: var(--blueOne);
    }

    .rookiesOrVets {
        height: 65px;
        vertical-align: middle;
    }

    .rivalLink {
        display: block;
        color: inherit;
        text-decoration: none;
    }

    .rivalLink:focus-visible, .headToHead:focus-visible {
        outline: 2px solid var(--blueOne);
        outline-offset: 2px;
    }

    .headToHead {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-height: 44px;
        padding: 0 0.6em;
        margin-top: 0.3em;
        font-size: 0.875rem;
        color: var(--accentInk);
        text-decoration: underline;
    }

    .infoRival:hover .infoIcon {
        box-shadow: 0 0 6px 4px var(--aaa);
        border: 1px solid var(--aaa);
    }

    .rival {
        height: 100%;
    }

    .rebuildOrWin {
        height: 70px;
    }

    .valuePosition {
        line-height: 70px;
        font-size: 25px;
        color: var(--fff);
    }

    .QB {
        background-color: var(--QB);
    }

    .WR {
        background-color: var(--WR);
    }

    .RB {
        background-color: var(--RB);
    }

    .TE {
        background-color: var(--TE);
    }

    .Picks {
        background: #73b647;
    }
    .K {
        background-color: var(--K);
    }

    .DEF {
        background-color: var(--DEF);
    }

    .CB {
        background-color: #ffcc7a;
    }

    .SS {
        background-color: #b7a1db;
    }

    .FS {
        background-color: #ebe7b3;
    }

    .DE {
        background-color: #b1d0e9;
    }

    .DL {
        background-color: #c392d3;
    }

    .LB {
        background-color: #98c097;
    }

    .favoritePlayer {
        height: 65px;
        vertical-align: bottom;
    }

    /* media queries */

    @media (max-width: 731px) {
        .infoSlot {
            margin: 2em 3em 0;
        }
    }

    @media (max-width: 558px) {
        .infoSlot {
            margin: 2em 2em 0;
        }
    }

    @media (max-width: 461px) {
        .infoSlot {
            margin: 2em 1em 0;
        }
    }
</style>

<div class="fantasyInfos">
    <!-- Rookies or Vets (optional) -->
    {#if viewManager.rookieOrVets}
        <div class="infoSlot">
            <div class="infoLabel">
                Rookie or Vet Preference
            </div>
            <div class="infoIcon">
                <img class="rookiesOrVets" src="/{viewManager.rookieOrVets}.png" alt="rookie or vet preference"/>
            </div>
            <div class="infoAnswer">
                {viewManager.rookieOrVets}
            </div>
        </div>
    {/if}
    <!-- Favorite fantasy position (optional) -->
    {#if viewManager.valuePosition}
        <div class="infoSlot">
            <div class="infoLabel">
                Favorite Fantasy Asset
            </div>
            <div class="infoIcon {viewManager.valuePosition}">
                <span class="valuePosition">{viewManager.valuePosition}</span>
            </div>
        </div>
    {/if}
    {#if viewManager.tradingScale}
        <!-- Trading Scale -->
        <div class="infoSlot">
            <div class="infoLabel">
                Desire to Trade
            </div>
            <div class="infoIcon">
                <span class="tradingScale">{viewManager.tradingScale}</span>
            </div>
            <div class="infoAnswer">
                {viewManager.tradingScale} out of 10
            </div>
        </div>
    {/if}
    <!-- Favorite player (optioonal) -->
    {#if viewManager.favoritePlayer}
        <div class="infoSlot">
            <div class="infoLabel">
                Favorite Player
            </div>
            <div class="infoIcon playerIcon">
                <img class="favoritePlayer" src="https://sleepercdn.com/content/nfl/players/{viewManager.favoritePlayer}.jpg" alt="favorite player"/>
            </div>
            <div class="infoAnswer">
                {players[viewManager.favoritePlayer].fn} {players[viewManager.favoritePlayer].ln}
            </div>
        </div>
    {/if}
    <!-- Rebuild Mod (optional) -->
    {#if viewManager.mode}
        <div class="infoSlot">
            <div class="infoLabel">
                Win Now or Rebuild?
            </div>
            <div class="infoIcon">
                <img class="rebuildOrWin" src="/{viewManager.mode.replace(' ', '%20')}.png" alt="win now or rebuild"/>
            </div>
            <div class="infoAnswer">
                {viewManager.mode}
            </div>
        </div>
    {/if}
    <!-- Rival -->
    <div class="infoSlot infoRival">
        <a class="rivalLink" href={rivalHref}>
            <div class="infoLabel">
                Rival
            </div>
            <div class="infoIcon">
                <img class="rival" src="{viewManager.rival.image}" alt="rival"/>
            </div>
            <div class="infoAnswer">
                {viewManager.rival.name}
            </div>
        </a>
        {#if headToHeadHref}
            <a class="headToHead" href={headToHeadHref}>Head-to-head</a>
        {/if}
    </div>
</div>