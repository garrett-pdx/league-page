"""
Lineups for any Sleeper roster shape: what a slot accepts, Sleeper's own "potential points"
greedy, and the true best legal lineup.

One module, imported by derive-site-data.py (and through it derive-narratives.py) and by
week-facts.py, so every figure the site and the blog publish about benched points, optimal
lineups and efficiency comes from the same definition. Stdlib only, Python 3.7 compatible.

    from lineup import slot_accepts, starters, sleeper_greedy, best_assignment

Two answers, on purpose:

  * sleeper_greedy() reproduces Sleeper's `potential_points`: walk the starting slots in roster
    order and give each the highest scorer still unused who may fill it. Its season sum is
    checked against Sleeper's figure, which is how we know the slot rules below are right.
  * best_assignment() is the true optimum, solved as an assignment problem. With overlapping
    flex slots (FLEX, SUPER_FLEX, WRRB_FLEX, REC_FLEX, IDP_FLEX) and multi-position players,
    the greedy can sit below it, and the optimum is the honest "best lineup".
"""

# Which player positions each Sleeper starting slot accepts. A slot not listed accepts the
# position of the same name, so a new single-position slot works without a change here.
SLOT_ELIGIBLE = {
    "QB": {"QB"},
    "RB": {"RB"},
    "WR": {"WR"},
    "TE": {"TE"},
    "K": {"K"},
    "DEF": {"DEF"},
    "FLEX": {"RB", "WR", "TE"},
    "WRRB_FLEX": {"WR", "RB"},
    "REC_FLEX": {"WR", "TE"},
    "SUPER_FLEX": {"QB", "RB", "WR", "TE"},
    "DL": {"DL"},
    "LB": {"LB"},
    "DB": {"DB"},
    "IDP_FLEX": {"DL", "LB", "DB"},
}

# Roster spots that are not starting slots.
NON_STARTING = {"BN", "IR", "TAXI"}

# Player positions as Sleeper reports them, mapped onto the positions slots ask for. IDP
# players carry their football position (DE, CB, ...); slots ask for DL, LB or DB.
POSITION_ALIAS = {
    "FB": "RB",
    "DE": "DL", "DT": "DL", "NT": "DL",
    "OLB": "LB", "ILB": "LB", "MLB": "LB",
    "CB": "DB", "S": "DB", "SS": "DB", "FS": "DB",
}


def normalize(position):
    return POSITION_ALIAS.get(position, position) if position else None


def slot_accepts(slot):
    return SLOT_ELIGIBLE.get(slot, {slot})


def starters(roster_positions):
    """The starting slots, in roster order, from a season's roster_positions."""
    return [s for s in (roster_positions or []) if s not in NON_STARTING]


def _can_fill(slot, positions):
    return bool(positions & slot_accepts(slot))


def sleeper_greedy(points, slots, eligible):
    """
    Sleeper's potential points: sort the roster by points (ties by player ID), then fill the
    slots in roster order, each with the best unused player who can play it.

    points:   {player_id: points}
    eligible: player_id -> set of positions he may fill
    Returns (total, [(slot, player_id, points), ...]).
    """
    pool = sorted(((pts or 0.0, str(pid)) for pid, pts in (points or {}).items()),
                  key=lambda x: (-x[0], x[1]))
    used, chosen, total = set(), [], 0.0
    for slot in slots:
        for pts, pid in pool:
            if pid in used:
                continue
            if _can_fill(slot, eligible(pid)):
                used.add(pid)
                chosen.append((slot, pid, pts))
                total += pts
                break
    return total, chosen


def _hungarian(cost):
    """
    Minimum-cost assignment of every row to a distinct column (rows <= columns). Integer
    costs. Returns col[i] for each row i. The classic O(n^2 m) potentials method.
    """
    n, m = len(cost), len(cost[0])
    inf = float("inf")
    u, v = [0] * (n + 1), [0] * (m + 1)
    p, way = [0] * (m + 1), [0] * (m + 1)
    for i in range(1, n + 1):
        p[0] = i
        j0 = 0
        minv = [inf] * (m + 1)
        used = [False] * (m + 1)
        while True:
            used[j0] = True
            i0, delta, j1 = p[j0], inf, 0
            for j in range(1, m + 1):
                if not used[j]:
                    cur = cost[i0 - 1][j - 1] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j], way[j] = cur, j0
                    if minv[j] < delta:
                        delta, j1 = minv[j], j
            for j in range(m + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while True:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break
    col = [0] * n
    for j in range(1, m + 1):
        if p[j]:
            col[p[j] - 1] = j - 1
    return col


def best_assignment(points, slots, eligible):
    """
    The highest-scoring legal lineup. Every slot gets a distinct eligible player or stays empty
    (an empty slot scores zero, which beats a negative score). Exact for any mix of flex slots
    and multi-position players.

    Returns (total, [(slot, player_id, points), ...]) with empty slots left out.
    """
    if not slots:
        return 0.0, []
    players = [(str(pid), pts or 0.0) for pid, pts in (points or {}).items()]
    big = 10 ** 9
    # Columns: one per player, then one "empty" column per slot. Costs in integer hundredths.
    cost = []
    for slot in slots:
        acc = slot_accepts(slot)
        row = [-int(round(pts * 100)) if (eligible(pid) & acc) else big for pid, pts in players]
        row += [0] * len(slots)
        cost.append(row)
    col = _hungarian(cost)
    chosen, total = [], 0.0
    for i, slot in enumerate(slots):
        j = col[i]
        if j < len(players) and cost[i][j] != big:
            pid, pts = players[j]
            chosen.append((slot, pid, pts))
            total += pts
    return total, chosen
