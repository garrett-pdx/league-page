import { getLeagueData } from './leagueData';
import { getLeagueRosters } from './leagueRosters';
import { waitForAll } from './multiPromise';
import { get } from 'svelte/store';
import { awards } from '$lib/stores';

export const getAwards = async () => {
	if(get(awards).length) {
		return get(awards);
	}
	const leagueData = await getLeagueData().catch((err) => { console.error(err); });

	let previousSeasonID = leagueData.status == "complete" ? leagueData.league_id : leagueData.previous_league_id;

	const podiums = await getPodiums(previousSeasonID);

	awards.update(() => podiums);

	return podiums;
}

const getPodiums = async (previousSeasonID) => {
	const podiums = [];

	while(previousSeasonID && previousSeasonID != 0) {
		// use the previous season ID to get the previous league, roster, user, and bracket data
		const previousSeasonData = await getPreviousLeagueData(previousSeasonID);

		const {
			losersData,
			winnersData,
			year,
			previousRosters,
			numDivisions,
			playoffRounds,
			toiletRounds,
			leagueMetadata
		} = previousSeasonData;

		previousSeasonID = previousSeasonData.previousSeasonID;

		const divisions = buildDivisionsAndManagers({previousRosters, leagueMetadata, numDivisions});

		// add manager to division obj and convert to array
		const divisionArr = []
		for(const key in divisions) {
			divisionArr.push(divisions[key]);
		}

		const finalsMatch = winnersData.filter(m => m.r == playoffRounds && m.t1_from.w)[0];
		const champion = finalsMatch.w;
		const second = finalsMatch.l;
	
		const runnersUpMatch = winnersData.filter(m => m.r == playoffRounds && m.t1_from.l)[0];
		const third = runnersUpMatch.w;

		const toiletBowlMatch = losersData.filter(m => m.r == toiletRounds && (!m.t1_from || m.t1_from.w))[0];
		const toilet = toiletBowlMatch.w

		if(!champion) {
			continue;
		}

		const podium = {
			year,
			champion,
			second,
			third,
			divisions: divisionArr,
			toilet
		}
		podiums.push(podium);
	}
	return podiums;
}

// fetch the previous season's data from sleeper
const getPreviousLeagueData = async (previousSeasonID) => {
	const resPromises = [
		fetch(`https://api.sleeper.app/v1/league/${previousSeasonID}`, {compress: true}),
		getLeagueRosters(previousSeasonID),
		fetch(`https://api.sleeper.app/v1/league/${previousSeasonID}/losers_bracket`, {compress: true}),
		fetch(`https://api.sleeper.app/v1/league/${previousSeasonID}/winners_bracket`, {compress: true}),
	]

	const [leagueRes, rostersData, losersRes, winnersRes] = await waitForAll(...resPromises).catch((err) => { console.error(err); });

	if(!leagueRes.ok || !losersRes.ok || !winnersRes.ok) {
		throw new Error(data);
	}

	const jsonPromises = [
		leagueRes.json(),
		losersRes.json(),
		winnersRes.json(),
	]

	const [prevLeagueData, losersData, winnersData] = await waitForAll(...jsonPromises).catch((err) => { console.error(err); });

	const year = prevLeagueData.season;

	const previousRosters = rostersData.rosters;

	const numDivisions = prevLeagueData.settings.divisions || 1;

	previousSeasonID = prevLeagueData.previous_league_id;

	const playoffRounds = winnersData[winnersData.length - 1].r
	const toiletRounds = losersData[losersData.length - 1].r

	return {
		losersData,
		winnersData,
		year,
		previousRosters,
		numDivisions,
		previousSeasonID,
		playoffRounds,
		toiletRounds,
		leagueMetadata: prevLeagueData.metadata
	}
}

// determine division champions and construct previousManagers object
const buildDivisionsAndManagers = ({previousRosters, leagueMetadata, numDivisions}) => {
	const divisions = {};

	for(let i = 1; i <= numDivisions; i++) {
		divisions[i] = {
			name: leagueMetadata ? leagueMetadata[`division_${i}`] : null,
			wins: -1,
			points: -1
		}
	}

	for(const rosterID in previousRosters) {
		const rSettings = previousRosters[rosterID].settings;
        const div = !rSettings.division || rSettings.division > numDivisions ? 1 : rSettings.division;
		/*
		Upstream compares points with `==` on a wins tie, not `>`. That means a tied team only
		displaces the incumbent when its points are EXACTLY equal -- which essentially never
		happens -- so the award silently went to whichever roster the loop reached first, i.e.
		the lowest roster ID.

		It changed a real result here. In 2022 Gurret (roster 1, 11-4, 1747.50) and
		jonahcartwright (roster 6, 11-4, 1762.54) tied on wins. Roster 1 set the baseline, and
		roster 6 could not displace it because 1762.54 != 1747.50, so the site credited the top
		seed to Gurret for four years. jonahcartwright outscored him by 15.04 and earned it.

		`>` is also the tiebreak the rest of the project already documents -- record, then
		points for -- which is how final_standings in static/data/ is derived.
		*/
		if(rSettings.wins > divisions[div].wins || (rSettings.wins == divisions[div].wins && (rSettings.fpts  + rSettings.fpts_decimal / 100)  > divisions[div].points)) {
			divisions[div].points = rSettings.fpts  + rSettings.fpts_decimal / 100;
			divisions[div].wins = rSettings.wins;
			divisions[div].rosterID = rosterID;
		}
	}

	return divisions;
}