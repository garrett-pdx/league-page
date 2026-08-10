<script>
    import { leagueName } from '$lib/utils/helper';
    let one, oneOne, oneTwo;
    let two, twoOne, twoTwo;
    let three, threeOne, threeTwo;
    let four, fourOne, fourTwo, fourThree, fourFour, fourFive;
    let five, fiveOne, fiveTwo;
    let six, sixOne;
    let seven, sevenOne, sevenTwo, sevenThree;
    let eight, eightOne, eightTwo;
    let nine, nineOne;

    const goToSection = (section) => {
        const top = section.getBoundingClientRect().top + window.pageYOffset;
        window.scrollTo({left: 0, top, behavior: 'smooth'});
    }
</script>

<style>
    .constitution {
        position: relative;
        z-index: 1;
        width: 92%;
        max-width: 800px;
        margin: 8em auto 10em;
    }

    h1 {
        font-size: 2em;
        line-height: 1.2em;
        text-align: center;
        margin: 2em 0 1.5em;
    }

    h2 {
        font-size: 1.5em;
        line-height: 1.2em;
    }

    h3 {
        text-decoration: underline;
        font-size: 1.3em;
        line-height: 1.2em;
    }

    h4 {
        text-decoration: underline;
        margin-left: 2em;
        font-size: 1.2em;
        line-height: 1.2em;
    }

    h5 {
        margin-left: 6em;
        font-size: 0.8em;
        line-height: 1.1em;
    }

    .subBlock {
        margin-left: 2.4em;
    }

    .sectionHeading {
        margin: 4em 0 1.5em;
    }

    .subSectionHeading {
        margin: 1.5em 0 1.5em;
    }

    .underscore {
        text-decoration: underline;
    }

    .right {
        text-align: right;
    }

    .positionMaximums td {
        min-width: 3em;
    }

    .noUnderscore {
        text-decoration: none;
    }

    /* The table of contents is a real <nav> of <button>s rather than a stack of
       clickable <h3>/<h4>. Two reasons: headings here duplicated every section
       title in the document outline, and click-only headings were completely
       unreachable by keyboard. Styled to match what they replaced. */
    .tocList,
    .tocSubList {
        list-style: none;
        margin: 0;
        padding: 0;
    }

    .tocSubList {
        margin-left: 2em;
    }

    .tocLink {
        background: none;
        border: none;
        padding: 0.15em 0;
        font-family: inherit;
        color: inherit;
        cursor: pointer;
        text-align: left;
        display: block;
        line-height: 1.2em;
    }

    .tocSection {
        font-size: 1.3em;
        font-weight: 700;
        margin-top: 0.9em;
    }

    .tocSub {
        font-size: 1.2em;
    }

    .tocLink:hover {
        color: #00316b;
    }

    .tocLink:focus-visible {
        outline: 2px solid #00316b;
        outline-offset: 2px;
        border-radius: 2px;
    }

    p {
        /* was a hardcoded #777, which lands at ~3.6-4.2:1 on this page's
           gradient in both themes and fails AA for body text. --g555 is the
           theme-aware token the rest of the site uses. */
        color: var(--g555);
    }
</style>

<div class="constitution">
    <h1 class="noUnderscore">{leagueName.toUpperCase()} CONSTITUTION</h1>

    <nav class="toc" aria-label="Table of contents">
        <h2 class="noUnderscore">TABLE OF CONTENTS</h2>
        <ul class="tocList">
            <li>
                <button type="button" class="tocLink tocSection" onclick={() => goToSection(one)}>Section 1: The League</button>
                <ul class="tocSubList">
                    <li><button type="button" class="tocLink tocSub" onclick={() => goToSection(oneOne)}>1.1 Format</button></li>
                    <li><button type="button" class="tocLink tocSub" onclick={() => goToSection(oneTwo)}>1.2 Commissioner</button></li>
                </ul>
            </li>
            <li>
                <button type="button" class="tocLink tocSection" onclick={() => goToSection(two)}>Section 2: Rosters and Lineups</button>
                <ul class="tocSubList">
                    <li><button type="button" class="tocLink tocSub" onclick={() => goToSection(twoOne)}>2.1 Starting Lineup</button></li>
                    <li><button type="button" class="tocLink tocSub" onclick={() => goToSection(twoTwo)}>2.2 Bench and Injured Reserve</button></li>
                </ul>
            </li>
            <li>
                <button type="button" class="tocLink tocSection" onclick={() => goToSection(three)}>Section 3: Scoring</button>
                <ul class="tocSubList">
                    <li><button type="button" class="tocLink tocSub" onclick={() => goToSection(threeOne)}>3.1 Scoring Values</button></li>
                    <li><button type="button" class="tocLink tocSub" onclick={() => goToSection(threeTwo)}>3.2 No Kickers, No Defenses</button></li>
                </ul>
            </li>
            <li>
                <button type="button" class="tocLink tocSection" onclick={() => goToSection(four)}>Section 4: Keepers</button>
                <ul class="tocSubList">
                    <li><button type="button" class="tocLink tocSub" onclick={() => goToSection(fourOne)}>4.1 How Many</button></li>
                    <li><button type="button" class="tocLink tocSub" onclick={() => goToSection(fourTwo)}>4.2 Keeper Cost</button></li>
                    <li><button type="button" class="tocLink tocSub" onclick={() => goToSection(fourThree)}>4.3 Inflation</button></li>
                    <li><button type="button" class="tocLink tocSub" onclick={() => goToSection(fourFour)}>4.4 Undrafted Players</button></li>
                    <li><button type="button" class="tocLink tocSub" onclick={() => goToSection(fourFive)}>4.5 Two Keepers, Same Round</button></li>
                </ul>
            </li>
            <li>
                <button type="button" class="tocLink tocSection" onclick={() => goToSection(five)}>Section 5: The Draft</button>
                <ul class="tocSubList">
                    <li><button type="button" class="tocLink tocSub" onclick={() => goToSection(fiveOne)}>5.1 Draft Format</button></li>
                    <li><button type="button" class="tocLink tocSub" onclick={() => goToSection(fiveTwo)}>5.2 Keepers on the Board</button></li>
                </ul>
            </li>
            <li>
                <button type="button" class="tocLink tocSection" onclick={() => goToSection(six)}>Section 6: Waivers and Free Agency</button>
                <ul class="tocSubList">
                    <li><button type="button" class="tocLink tocSub" onclick={() => goToSection(sixOne)}>6.1 FAAB</button></li>
                </ul>
            </li>
            <li>
                <button type="button" class="tocLink tocSection" onclick={() => goToSection(seven)}>Section 7: Trades</button>
                <ul class="tocSubList">
                    <li><button type="button" class="tocLink tocSub" onclick={() => goToSection(sevenOne)}>7.1 Trading</button></li>
                    <li><button type="button" class="tocLink tocSub" onclick={() => goToSection(sevenTwo)}>7.2 Trade Deadline</button></li>
                    <li><button type="button" class="tocLink tocSub" onclick={() => goToSection(sevenThree)}>7.3 Trading Draft Picks</button></li>
                </ul>
            </li>
            <li>
                <button type="button" class="tocLink tocSection" onclick={() => goToSection(eight)}>Section 8: Postseason</button>
                <ul class="tocSubList">
                    <li><button type="button" class="tocLink tocSub" onclick={() => goToSection(eightOne)}>8.1 Playoffs</button></li>
                    <li><button type="button" class="tocLink tocSub" onclick={() => goToSection(eightTwo)}>8.2 Consolation Bracket</button></li>
                </ul>
            </li>
            <li>
                <button type="button" class="tocLink tocSection" onclick={() => goToSection(nine)}>Section 9: League Votes</button>
                <ul class="tocSubList">
                    <li><button type="button" class="tocLink tocSub" onclick={() => goToSection(nineOne)}>9.1 Making Changes</button></li>
                </ul>
            </li>
        </ul>
    </nav>

    <hr />

    <h2 class="sectionHeading" bind:this={one}>Section 1 The League</h2>

    <h3 class="subSectionHeading" bind:this={oneOne}>1.1 Format</h3>
    <p>{leagueName} is a ten-team keeper league on Sleeper, running since 2022. It is a keeper league, not a dynasty league: every season the entire player pool returns to the draft board except the players each manager elects to keep, and those keepers cost draft capital (see Section 4).</p>
    <p>The regular season runs from Week 1 through Week 15. The postseason runs Weeks 16 and 17.</p>

    <h3 class="subSectionHeading" bind:this={oneTwo}>1.2 Commissioner</h3>
    <p>Garrett (Sleeper handle <span class="underscore">Gurret</span>) is the commissioner. The commissioner administers the league on Sleeper, sets the schedule and draft, and rules on anything this document does not cover.</p>

    <h2 class="sectionHeading" bind:this={two}>Section 2 Rosters and Lineups</h2>

    <h3 class="subSectionHeading" bind:this={twoOne}>2.1 Starting Lineup</h3>
    <p>Each team starts eight players every week:</p>
    <ul>
        <li>1 &times; QB</li>
        <li>2 &times; RB</li>
        <li>2 &times; WR</li>
        <li>1 &times; TE</li>
        <li>2 &times; FLEX (RB, WR or TE)</li>
    </ul>
    <p>Lineups lock at each player's individual kickoff. A player left in a starting slot after his game has finished scores zero for that slot; it is each manager's responsibility to set a valid lineup.</p>

    <h3 class="subSectionHeading" bind:this={twoTwo}>2.2 Bench and Injured Reserve</h3>
    <p>Rosters carry six bench spots, for fourteen roster spots in total, plus two Injured Reserve slots that do not count against the roster limit.</p>
    <p>A player may be placed on IR only while Sleeper lists him as Out, Not Active (PUP/NFI), Suspended, or on the COVID list. Players listed as Doubtful or Did Not Report are not IR-eligible. A player who returns to active status must be moved off IR before he can be started.</p>

    <h2 class="sectionHeading" bind:this={three}>Section 3 Scoring</h2>

    <h3 class="subSectionHeading" bind:this={threeOne}>3.1 Scoring Values</h3>
    <p>The league scores half-PPR with six-point passing touchdowns.</p>
    <p><span class="underscore">Passing</span></p>
    <ul>
        <li>1 point per 25 passing yards</li>
        <li>6 points per passing touchdown</li>
        <li>&minus;2 points per interception thrown</li>
        <li>2 points per passing two-point conversion</li>
    </ul>
    <p><span class="underscore">Rushing and Receiving</span></p>
    <ul>
        <li>1 point per 10 rushing or receiving yards</li>
        <li>6 points per rushing or receiving touchdown</li>
        <li>0.5 points per reception</li>
        <li>2 points per two-point conversion, rushing or receiving</li>
    </ul>
    <p><span class="underscore">Miscellaneous</span></p>
    <ul>
        <li>&minus;1 point per fumble lost</li>
        <li>6 points per fumble recovered for a touchdown</li>
    </ul>
    <p>There are no positional bonuses. Tight ends receive no premium above the standard half-point per reception.</p>

    <h3 class="subSectionHeading" bind:this={threeTwo}>3.2 No Kickers, No Defenses</h3>
    <p>There is no kicker slot and no team defense slot in this league. Neither position has a place in the starting lineup, and neither is drafted. Only quarterbacks, running backs, wide receivers and tight ends are relevant.</p>

    <h2 class="sectionHeading" bind:this={four}>Section 4 Keepers</h2>

    <h3 class="subSectionHeading" bind:this={fourOne}>4.1 How Many</h3>
    <p>Each team may keep up to two players from the previous season's roster. Keeping fewer than two, or none at all, is always allowed.</p>

    <h3 class="subSectionHeading" bind:this={fourTwo}>4.2 Keeper Cost</h3>
    <p>A keeper costs the round in which he was drafted the previous season. Keeping a player selected in the seventh round last year costs this year's seventh-round pick, and that pick is spent &mdash; the team does not pick in that round.</p>

    <h3 class="subSectionHeading" bind:this={fourThree}>4.3 Inflation</h3>
    <p>If the <span class="underscore">same manager</span> keeps the <span class="underscore">same player</span> two years running, the cost climbs by one round. A seventh-round keeper held a second straight year costs a sixth-round pick, then a fifth the year after, and so on. Cost cannot climb past the first round.</p>
    <p>Inflation follows the manager, not the roster. A player who was kept by a different team last season does not carry that inflation to his new team &mdash; his cost is simply the round he was drafted.</p>

    <h3 class="subSectionHeading" bind:this={fourFour}>4.4 Undrafted Players</h3>
    <p>A player who was not drafted last season &mdash; picked up off waivers or free agency during the year &mdash; costs a final-round pick to keep.</p>

    <h3 class="subSectionHeading" bind:this={fourFive}>4.5 Two Keepers, Same Round</h3>
    <p>If both of a team's keepers owe the same round, <span class="underscore">the manager chooses</span> which of the two moves up. That player's cost becomes one round earlier; the other keeps the original round.</p>
    <p>If the round the bumped player moves into is also occupied by one of that team's keepers, he continues moving up a round at a time until he lands on a round the team still holds. A keeper who would be pushed past the first round cannot be kept.</p>

    <h2 class="sectionHeading" bind:this={five}>Section 5 The Draft</h2>

    <h3 class="subSectionHeading" bind:this={fiveOne}>5.1 Draft Format</h3>
    <p>The draft is a fourteen-round snake draft with a two-minute pick timer. Draft picks may be traded (see Section 7).</p>

    <h3 class="subSectionHeading" bind:this={fiveTwo}>5.2 Keepers on the Board</h3>
    <p>Keepers occupy their cost round on the draft board before the draft begins. A team that keeps two players has two fewer picks to make.</p>
    <p>The league's <a href="https://garrett-pdx.github.io/keeper-draft-board/" target="_blank" rel="noopener">Keeper Draft Board</a> computes every team's keeper costs, shows what the rest of the league has locked in, and runs the draft itself.</p>

    <h2 class="sectionHeading" bind:this={six}>Section 6 Waivers and Free Agency</h2>

    <h3 class="subSectionHeading" bind:this={sixOne}>6.1 FAAB</h3>
    <p>Waivers run on a Free Agent Acquisition Budget. Each manager receives $100 for the season, and that budget is not replenished. Bids may be as low as $0, and the highest bid wins; Sleeper breaks ties by waiver priority.</p>
    <p>Claims clear on the league's weekly waiver run. Players who go unclaimed become free agents and can be added by anyone.</p>
    <p>FAAB dollars may be included in trades.</p>

    <h2 class="sectionHeading" bind:this={seven}>Section 7 Trades</h2>

    <h3 class="subSectionHeading" bind:this={sevenOne}>7.1 Trading</h3>
    <p>Players, draft picks and FAAB dollars may all be traded. Trades process immediately on acceptance &mdash; there is no review period and no automatic league vote.</p>
    <p>Trades are made in good faith between managers acting in their own competitive interest. The commissioner may reverse a trade only in the case of clear collusion or a manager acting against the integrity of the league.</p>

    <h3 class="subSectionHeading" bind:this={sevenTwo}>7.2 Trade Deadline</h3>
    <p>The trade deadline is Week 12. No trades of any kind may be made after the deadline passes, including trades involving only draft picks.</p>

    <h3 class="subSectionHeading" bind:this={sevenThree}>7.3 Trading Draft Picks</h3>
    <p>Draft picks must be traded <span class="underscore">one for one</span>. A trade that includes draft picks must send and receive the same number of them, so that every team goes into the draft holding the same total number of picks it started with.</p>
    <p>Rounds do not have to match &mdash; a third-round pick may be traded for a tenth. A team can therefore hold two picks in one round and none in another. What cannot change is the total.</p>
    <p>Picks may still be packaged with players or FAAB; the one-for-one requirement applies only to the picks themselves.</p>

    <h2 class="sectionHeading" bind:this={eight}>Section 8 Postseason</h2>

    <h3 class="subSectionHeading" bind:this={eightOne}>8.1 Playoffs</h3>
    <p>Four teams make the playoffs. The bracket runs two rounds across Weeks 16 and 17: semifinals in Week 16, then the championship in Week 17. The two Week 16 losers play a third-place game in Week 17.</p>

    <h3 class="subSectionHeading" bind:this={eightTwo}>8.2 Consolation Bracket</h3>
    <p>Teams that miss the playoffs play a consolation bracket over the same two weeks. It decides nothing, and everyone plays it anyway.</p>

    <h2 class="sectionHeading" bind:this={nine}>Section 9 League Votes</h2>

    <h3 class="subSectionHeading" bind:this={nineOne}>9.1 Making Changes</h3>
    <p>Any change to the league goes to a vote, and passes <span class="underscore">7&ndash;3</span>. That covers anything &mdash; scoring, roster spots, keeper rules, the draft, playoffs, league size. Any manager may put a change forward.</p>

</div>
