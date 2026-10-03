import { managers } from '$lib/utils/leagueInfo';

/*
Where a team's manager page is, as a URL -- for components that need a real <a href> instead of
upstream's click handler.

Ours, not upstream's. It follows gotoManager() in helperFunctions/universalFunctions.js
step for step (same year clamp, same managerID-then-rosterID order, same fallback to the
deprecated `roster` field) but returns the address instead of calling goto(). That matters
because a link can be opened in a new tab, shown on hover and reached with the Tab key; a
click handler on a div can do none of those.

Pass either a managerID (a Sleeper user_id) or a rosterID plus the season it belongs to --
roster IDs mean nothing across seasons, so the year decides whose roster it was.

Returns '/managers' (the directory) when the team has no entry in leagueInfo's `managers`,
where gotoManager would have gone to /manager?manager=-1 and been redirected there anyway.
*/
export const managerIndex = ({leagueTeamManagers, managerID, rosterID, year}) => {
    if(!managers.length) return -1;

    if(!year || year > leagueTeamManagers.currentSeason) {
        year = leagueTeamManagers.currentSeason;
    }

    if(managerID) {
        const index = managers.findIndex(m => m.managerID == managerID);
        if(index > -1) return index;
    }

    const roster = leagueTeamManagers.teamManagersMap?.[year]?.[rosterID];
    if(roster) {
        for(const mID of roster.managers) {
            const index = managers.findIndex(m => m.managerID == mID);
            if(index > -1) return index;
        }
    }

    // support for league pages still using the deprecated roster field
    if(rosterID) {
        return managers.findIndex(m => m.roster == rosterID);
    }
    return -1;
}

export const managerHref = (args) => {
    const index = managerIndex(args);
    return index > -1 ? `/manager?manager=${index}` : '/managers';
}
