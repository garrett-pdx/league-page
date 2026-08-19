<script>
    import { gotoManager } from '$lib/utils/helper';
	import { getAvatarFromTeamManagers, getNestedTeamNamesFromTeamManagers } from '$lib/utils/helperFunctions/universalFunctions';
	export let podium, leagueTeamManagers;

	const { year, champion, second, third, divisions, toilet } = podium;
</script>

<style>
	* {
		color: var(--g555);
	}

	h3 {
		margin: 2.5em 0 1.5em;
	}

	.awards {
		display: block;
		position: relative;
		width: 100%;
		z-index: 1;
	}

	#podium {
		width: 600px;
		height: 500px;
		position: relative;
		margin: 10px auto 30px;
	}

	.podiumImage {
		position: absolute;
		bottom: 0;
		left: 0;
		width: 100%;
		height: auto;
		z-index: 3;
	}

	.champ {
		position: absolute;
		width: 20%;
		height: auto;
		transform: translate(-50%, -50%);
		border-radius: 100%;
		border: 1px solid var(--bbb);
		background-color: var(--fff);
	}

	.laurel {
		position: absolute;
		width: 33%;
		height: auto;
		transform: translate(-50%, -50%);
		/*
		top, not bottom -- this is the second bug, not just a wrong number. .first anchors with
		`bottom: 70%` + translate(-50%,-50%); with `bottom` (rather than `top`), the transform's
		-50% is 50% of the ELEMENT'S OWN height, so two elements of different height (avatar 20%
		of podium width, laurel 33%) end up with different final centres even given the SAME
		bottom value -- confirmed by measuring both: matching bottom to .first's 70% left the
		laurel about 20px higher on the box than the avatar, not aligned. Anchoring from `top`
		instead makes the maths height-independent (top% alone IS the final centre, regardless
		of the element's own size), which is what the home page's version already does correctly.
		5.2% was read off .first's actual measured centre, not derived from the width percentages
		alone -- box-sizing: content-box means .champ's 1px border adds a couple of px to its
		rendered height beyond the pure 20%-of-width figure, which is exactly what a purely
		algebraic value would have missed. No breakpoint below re-declares this, and because
		#podium, .first and .laurel all scale together (podium's 600:500 ratio holds at every
		breakpoint), one percentage holds everywhere.
		*/
		top: 5.2%;
		left: 50%;
		pointer-events: none;
	}

	.first {
		bottom: 70%;
		left: 50%;
	}

	.second {
		bottom: 43%;
		left: 20%;
	}

	.third {
		bottom: 39%;
		left: 80%;
	}

	h3 {
		text-align: center;
	}

	.leaderBlock {
		position: relative;
		width: 80px;
		height: 119px;
		margin: 15px auto;
	}

	.divisions {
		display: flex;
		justify-content: space-around;
	}

	.divisionLeader {
		position: absolute;
		width: 70px;
		height: 70px;
		transform: translate(-50%, 0%);
		top: 0;
		left: 50%;
		border-radius: 100%;
		border: 1px solid var(--bbb);
		background-color: var(--fff);
		z-index: 3;
	}

	.medal {
		position: absolute;
		width: 40px;
		height: auto;
		transform: translate(-50%, 0%);
		bottom: 0;
		left: 50%;
		z-index: 2;
	}

	.toiletBowl {
		position: relative;
		width: 215px;
		height: 190px;
		margin: 10px auto;
	}

	.toiletWinner {
		position: absolute;
		width: 65px;
		height: 65px;
		transform: translate(-50%, 0%);
		top: 20px;
		left: 55%;
		border-radius: 100%;
		border: 1px solid var(--bbb);
		z-index: 3;
	}

	.toilet {
		position: absolute;
		width: 100%;
		height: auto;
		transform: translate(-50%, 0%);
		bottom: 0;
		left: 50%;
	}

	.label {
		white-space: nowrap;
		line-height: 1.1em;
		text-align: center;
		min-height: 34px;
		display: flex;
		flex-direction: column;
		justify-content: center;
		position: absolute;
		transform: translate(-50%, -50%);
		padding: 6px 30px;
		background-color: var(--fff);
		border: 1px solid var(--bbb);
        box-shadow: var(--shadowCard);
	}

	.firstLabel {
		bottom: 60%;
		left: 50%;
	}

	.secondLabel {
		bottom: 40%;
		left: 20%;
	}

	.thirdLabel {
		bottom: 36%;
		left: 80%;
	}

	.genLabel {
		white-space: nowrap;
		line-height: 1.1em;
		min-height: 34px;
		display: inline-flex;
		flex-direction: column;
		justify-content: center;
		text-align: center;
		margin: 15px auto 20px;
		padding: 6px 30px;
		background-color: var(--fff);
		border: 1px solid var(--bbb);
		box-shadow: var(--shadowCard);
	}

	.division {
		text-align: center;
	}

	.toiletParent {
		width: 100%;
		text-align: center;
		padding: 25px 0 40px;
		margin-top: 30px;
		box-shadow: 0 12px 9px -12px rgba(0,0,0,0.4);
	}

	.bannerWrap {
		position: relative;
		display: block;
		width: 65%;
		max-width: 450px;
		margin: 20px auto 0;
	}

	.banner {
		display: block;
		width: 100%;
	}

	.bannerText {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: 72%;
		text-align: center;
		font-family: var(--fontDisplay);
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		/* navy on the ribbon's gold measures 6.20, so this clears AA at any size */
		color: var(--goldOnFill);
		/* scales with the ribbon, which is a percentage of its container */
		font-size: clamp(0.85rem, 3.2vw, 1.6rem);
		line-height: 1;
		white-space: nowrap;
		pointer-events: none;
	}

	.toilet-banner {
		display: block;
		width: 50%;
		max-width: 350px;
		margin: 20px auto 0;
	}

	.clickable {
		cursor: pointer;
	}

	:global(.curOwner) {
		font-size: 0.75em;
		color: var(--bbb);
		font-style: italic;
	}

	@media (max-width: 680px) {
		.label {
			padding: 6px 8px;
		}
		.genLabel {
			padding: 6px 8px;
		}
	}

	@media (max-width: 630px) {
		.label {
			font-size: 0.9em;
		}
		.genLabel {
			font-size: 0.9em;
		}
	}

	@media (max-width: 610px) {
		#podium {
			width: 500px;
			height: 417px;
			position: relative;
			margin: 10px auto 30px;
		}

		.firstLabel {
			bottom: 58%;
		}

		.secondLabel {
			bottom: 35%;
		}

		.thirdLabel {
			bottom: 31%;
		}
	}

	@media (max-width: 535px) {
		.label {
			font-size: 0.8em;
		}
		.genLabel {
			font-size: 0.8em;
		}
	}

	@media (max-width: 520px) {
		.label {
			font-size: 0.7em;
			padding: 2px 4px;
		}
		.genLabel {
			font-size: 0.7em;
			padding: 2px 4px;
		}
	}

	@media (max-width: 510px) {
		#podium {
			width: 400px;
			height: 333px;
		}
	}

	@media (max-width: 425px) {
		.label {
			font-size: 0.6em;
		}
		.genLabel {
			font-size: 0.6em;
		}
	}

	@media (max-width: 410px) {
		#podium {
			width: 300px;
			height: 250px;
		}

		.firstLabel {
			bottom: 53%;
		}

		.secondLabel {
			bottom: 31%;
		}

		.thirdLabel {
			bottom: 27%;
		}
	}

	@media (max-width: 329px) {
		.label {
			font-size: 0.5em;
		}
		.genLabel {
			font-size: 0.5em;
		}
	}
</style>

<div class="awards">
	<h3>{year} Awards</h3>

	<!-- The ribbon is now decoration and the words are real markup, so they follow the display
	     font, can be selected and translated, and reach a screen reader as text rather than as
	     an alt attribute. The old banner.png had "Champion's Cup" baked into the bitmap. -->
	<div class="bannerWrap">
		<img src="/brand/banner.svg" class="banner" alt="" />
		<span class="bannerText">Champion's Cup</span>
	</div>

	<div id="podium">
		<img src="/podium.png" class="podiumImage" alt="podium" />

		<!-- champs -->
		<img src="{getAvatarFromTeamManagers(leagueTeamManagers, champion, year)}" class="first champ clickable" onclick={() => gotoManager({year, leagueTeamManagers, rosterID: champion})} alt="champion" />
		<img src="/brand/laurel.svg" class="laurel" alt="laurel" />
		<span class="label firstLabel clickable" onclick={() => gotoManager({year, leagueTeamManagers, rosterID: champion})}>{@html getNestedTeamNamesFromTeamManagers(leagueTeamManagers, year, champion)}</span>

		<img src="{getAvatarFromTeamManagers(leagueTeamManagers, second, year)}" class="second champ clickable" onclick={() => gotoManager({year, leagueTeamManagers, rosterID: second})} alt="2nd" />
		<span class="label secondLabel clickable" onclick={() => gotoManager({year, leagueTeamManagers, rosterID: second})}>{@html getNestedTeamNamesFromTeamManagers(leagueTeamManagers, year, second)}</span>

		<img src="{getAvatarFromTeamManagers(leagueTeamManagers, third, year)}" class="third champ clickable" onclick={() => gotoManager({year, leagueTeamManagers, rosterID: third})} alt="3rd" />
		<span class="label thirdLabel clickable" onclick={() => gotoManager({year, leagueTeamManagers, rosterID: third})}>{@html getNestedTeamNamesFromTeamManagers(leagueTeamManagers, year, third)}</span>
	</div>
	<div class="divisions">
		{#each divisions as division}
			{#if division.rosterID}
				<div class="division">
					{#if division.name}
						<h6>{division.name} Division</h6>
					{:else}
						<h6>Regular Season Champion</h6>
					{/if}
					<div class="leaderBlock">
						<img src="{getAvatarFromTeamManagers(leagueTeamManagers, division.rosterID, year)}" class="divisionLeader clickable" onclick={() => gotoManager({year, leagueTeamManagers, rosterID: division.rosterID})} alt="{division.name} champion" />
						<img src="/medal.png" class="medal" alt="champion" />
					</div>
					<span class="genLabel clickable" onclick={() => gotoManager({year, leagueTeamManagers, rosterID: division.rosterID})}>{@html getNestedTeamNamesFromTeamManagers(leagueTeamManagers, year, division.rosterID)}</span>
				</div>
			{/if}
		{/each}
	</div>

		<!-- Toilet Bowl -->
	{#if toilet}
		<div class="toiletParent">
			
			<img src="/toilet-banner.png" class="toilet-banner" alt="The Toilet Bowl" />

			<div class="toiletBowl">
				<img src="{getAvatarFromTeamManagers(leagueTeamManagers, toilet, year)}" class="toiletWinner clickable" onclick={() => gotoManager({year, leagueTeamManagers, rosterID: toilet})} alt="toilet bowl winner" />
				<img src="/toilet-bowl-2.png" class="toilet" alt="toilet bowl" />
			</div>
			<span class="genLabel clickable" onclick={() => gotoManager({year, leagueTeamManagers, rosterID: toilet})}>{@html getNestedTeamNamesFromTeamManagers(leagueTeamManagers, year, toilet)}</span>
		</div>
	{/if}
</div>