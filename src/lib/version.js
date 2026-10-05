/*
The engine version this site runs. Keep in sync with package.json; scripts/update-engine.py
replaces this file along with the rest of the engine. /api/checkVersion compares it with the
template's published package.json and the footer offers an update when that is newer.
*/
export const version = "1.0.1";
