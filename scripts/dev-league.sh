#!/bin/sh
# Serve the site for another league's directory, as scripts/try-league.sh writes it:
# <dir>/league.json (plus any prose and managers/ photos) and <dir>/data/.
#
#   npm run dev:league -- try-league/<league_id> [vite options]
#
# Runs alongside the normal dev server (port 5174 unless --port says otherwise).
set -eu
dir="$(cd "${1:?usage: npm run dev:league -- <dir> [vite options]}" && pwd)"
shift
LEAGUE_DIR="$dir" LEAGUE_DATA="$dir/data" exec npx vite dev --port 5174 "$@"
