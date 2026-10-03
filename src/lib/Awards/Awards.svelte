<script>
    import { gotoManager } from '$lib/utils/helper';
    import { managerHref } from '$lib/utils/managerLink';
    import { SectionHeading } from '$lib/Design';
	import { getAvatarFromTeamManagers, getNestedTeamNamesFromTeamManagers } from '$lib/utils/helperFunctions/universalFunctions';
	export let podium, leagueTeamManagers;

	const { year, champion, second, third, divisions, toilet } = podium;

	// The names under the podium on a phone, in place of the labels that sit over it on a wide
	// screen. Both are rendered; CSS shows one.
	const places = [['1st', champion], ['2nd', second], ['3rd', third]];
</script>

<style>
	* {
		color: var(--g555);
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
		margin: 0 auto 16px;
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
		margin: 8px auto 12px;
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
		padding: 12px 0 24px;
		margin-top: 16px;
		box-shadow: 0 12px 9px -12px rgba(0,0,0,0.4);
	}

	.bannerWrap {
		position: relative;
		display: block;
		width: 65%;
		max-width: 450px;
		margin: 8px auto 0;
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
		margin: 12px auto 0;
	}

	.clickable {
		cursor: pointer;
	}

	:global(.curOwner) {
		font-size: 12px;
		color: var(--g555);
		font-style: italic;
	}

	/*
	The three place labels sit over the podium picture. Below 650px the picture is 500px and then
	300px wide, and a team name does not fit over an avatar a fifth of that wide: the labels
	covered the avatars. The type used to shrink to 0.5em to try to fit. Instead the labels are
	hidden there and the same names are listed under the podium as ordinary rows.
	*/
	.podiumNames {
		display: none;
		list-style: none;
		margin: 0 auto 8px;
		padding: 0;
		width: 92%;
		max-width: 420px;
	}

	.podiumNames a {
		display: flex;
		align-items: center;
		gap: 0.8em;
		min-height: 44px;
		padding: 4px 12px;
		box-sizing: border-box;
		text-decoration: none;
		color: var(--navy700);
		line-height: 1.15;
		border-bottom: 1px solid var(--accentBorder);
	}

	.podiumNames .teamName {
		color: var(--navy700);
	}

	.podiumNames li:last-child a {
		border-bottom: none;
	}

	.podiumNames .place {
		flex: 0 0 2.4em;
		font-family: var(--fontDisplay);
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--accentInk);
	}

	@media (max-width: 680px) {
		.label {
			padding: 6px 8px;
		}
		.genLabel {
			padding: 6px 8px;
		}
	}

	@media (max-width: 650px) {
		.label {
			display: none;
		}

		.podiumNames {
			display: block;
		}

		/* A division or toilet bowl label may be a long name plus the current one beneath it. */
		.genLabel {
			white-space: normal;
			max-width: 90%;
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

	@media (max-width: 510px) {
		#podium {
			width: 400px;
			height: 333px;
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

</style>

<div class="awards">
	<SectionHeading level={3} accent="gold">{year} Awards</SectionHeading>

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
	<ul class="podiumNames">
		{#each places as [place, rosterID]}
			<li><a href="{managerHref({year, leagueTeamManagers, rosterID})}"><span class="place">{place}</span><span class="teamName">{@html getNestedTeamNamesFromTeamManagers(leagueTeamManagers, year, rosterID)}</span></a></li>
		{/each}
	</ul>
	<div class="divisions">
		{#each divisions as division}
			{#if division.rosterID}
				<div class="division">
					{#if division.name}
						<SectionHeading level={4} rule={false}>{division.name} Division</SectionHeading>
					{:else}
						<!-- A record earns a seed, not a trophy -- see ManagerAwards.svelte. -->
						<SectionHeading level={4} rule={false}>No. 1 Seed</SectionHeading>
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