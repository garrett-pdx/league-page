/*
How often the Free Agents Refresh button can force a fresh pull of the list. Shared by the page
(which sends the current window number as ?fresh=) and api/fetch_free_agents (which only accepts
the current window +/-1). Lengthening it means fewer 15MB Sleeper pulls and ESPN fan-outs.
*/
export const REFRESH_WINDOW_MS = 5 * 60 * 1000;

export const currentRefreshWindow = () => Math.floor(Date.now() / REFRESH_WINDOW_MS);
