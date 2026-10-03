<script>
    /*
    A finished season's playoff bracket, read-only: the four-team winners bracket (semifinals,
    then the final and the third-place game) and the consolation side (5th to 8th). Built from
    seasonBracket() in seasonData.js, which maps the bracket's roster IDs through that season's
    own roster map and takes each score from games.json.

    New rather than upstream's Brackets.svelte, which expects Sleeper's live data shapes and a
    season in progress.
    */
    import Person from './Person.svelte';

    export let bracket;
    export let people;

    const pts = (n) => n === null || n === undefined ? '–' : n.toFixed(2);
</script>

<style>
    .side {
        width: 94%;
        max-width: 860px;
        margin: 0 auto 1.5em;
    }

    .sideTitle {
        font-family: var(--fontDisplay);
        font-size: 0.85rem;
        font-weight: 500;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--g555);
        margin: 0 0 0.6em;
        text-align: center;
    }

    .rounds {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1rem 1.5rem;
        align-items: center;
    }

    .round { display: grid; gap: 0.8rem; }

    .roundTitle {
        font-family: var(--fontDisplay);
        font-size: 0.8rem;
        font-weight: 500;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--g555);
        margin: 0;
    }

    .game {
        background-color: var(--fff);
        border-radius: var(--radiusMd);
        box-shadow: var(--shadowCard);
        overflow: hidden;
    }

    .gameLabel {
        display: block;
        padding: 0.35rem 0.75rem;
        font-family: var(--fontDisplay);
        font-size: 0.78rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--g555);
        background-color: var(--navy050);
    }

    .title .gameLabel {
        background-color: var(--goldFill);
        color: var(--goldOnFill);
        font-weight: 600;
    }

    .team {
        display: grid;
        grid-template-columns: 1.6rem minmax(0, 1fr) auto;
        align-items: center;
        gap: 0.4rem;
        padding: 0 0.75rem;
        border-top: 1px solid var(--eee);
        color: var(--g555);
    }

    .seed {
        font-size: 0.8rem;
        color: var(--g555);
        text-align: center;
        font-variant-numeric: tabular-nums;
    }

    .score {
        font-variant-numeric: tabular-nums;
        white-space: nowrap;
    }

    .won { color: var(--g111); }
    .won .score { font-weight: 700; color: var(--navy700); }

    .srOnly {
        position: absolute;
        width: 1px;
        height: 1px;
        overflow: hidden;
        clip: rect(0 0 0 0);
        white-space: nowrap;
    }

    @media (max-width: 600px) {
        .rounds { grid-template-columns: 1fr; }
    }
</style>

{#each [['Playoffs', bracket.winners], ['Consolation bracket', bracket.losers]] as [title, rounds]}
    {#if rounds.length}
        <section class="side" aria-label={title}>
            <h4 class="sideTitle">{title}</h4>
            <div class="rounds">
                {#each rounds as round}
                    <div class="round">
                        <p class="roundTitle">{round.label}</p>
                        {#each round.games as game}
                            <div class="game" class:title={game.place === 1}>
                                <span class="gameLabel">{game.label}</span>
                                {#each [game.a, game.b] as side}
                                    <div class="team" class:won={side.won}>
                                        <span class="seed" title="Regular-season seed">{side.seed ?? ''}</span>
                                        <Person person={people[side.user_id]} size={26} />
                                        <span class="score">{pts(side.pf)}{#if side.won}<span class="srOnly"> (won)</span>{/if}</span>
                                    </div>
                                {/each}
                            </div>
                        {/each}
                    </div>
                {/each}
            </div>
        </section>
    {/if}
{/each}
