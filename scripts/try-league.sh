#!/bin/sh
# Run the whole data pipeline against any Sleeper league, in a scratch directory, without
# touching this repo's league/ or static/data/.
#
#   scripts/try-league.sh <sleeper_league_id> [dir]
#
# Writes <dir>/league.json (a minimal config), <dir>/data/ (the dataset) and <dir>/docs/
# (league-lore.md), plus a log per step. Exits non-zero at the first step that fails, which
# is usually a self-check naming what the engine does not yet understand about the league.
# Default dir: ./try-league/<id> (gitignored).
set -eu

id="${1:?usage: scripts/try-league.sh <sleeper_league_id> [dir]}"
root="$(cd "$(dirname "$0")/.." && pwd)"
dir="${2:-$root/try-league/$id}"
mkdir -p "$dir/data" "$dir/docs"

name=$(curl -s --max-time 20 "https://api.sleeper.app/v1/league/$id" | python3 -c 'import json,sys; print(json.load(sys.stdin)["name"])')
printf '{\n  "sleeperLeagueId": "%s",\n  "name": %s\n}\n' "$id" "$(printf '%s' "$name" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')" > "$dir/league.json"

export LEAGUE_CONFIG="$dir/league.json" LEAGUE_DATA="$dir/data" LEAGUE_DOCS="$dir/docs"

run() {
    step="$1"; shift
    if "$@" > "$dir/$step.log" 2>&1; then
        echo "ok    $step"
    else
        echo "FAIL  $step  (see $dir/$step.log)"
        tail -20 "$dir/$step.log" | sed 's/^/      /'
        exit 1
    fi
}

echo "$name ($id) -> $dir"
run pull python3 "$root/scripts/pull-league-history.py"
run derive-site-data python3 "$root/scripts/derive-site-data.py"
run derive-narratives python3 "$root/scripts/derive-narratives.py"
